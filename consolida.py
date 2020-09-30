import io
import json
import os
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import groupby
from pathlib import Path
from signal import SIGINT

import rows
import scrapy
from rows.utils import load_schema
from scrapy.exceptions import CloseSpider

import demographics

DATA_PATH = Path(__file__).parent / "data"
ERROR_PATH = DATA_PATH / "error"


class ConsolidaSpider(scrapy.Spider):
    name = "consolida"
    base_url = "https://brasil.io/covid19/import-data/{uf}/"
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    }

    def __init__(self, boletim_filename, caso_filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boletim_writer = rows.utils.CsvLazyDictWriter(boletim_filename)
        self.caso_writer = rows.utils.CsvLazyDictWriter(caso_filename)
        self.errors = defaultdict(list)

    def start_requests(self):
        for state in demographics.states():
            yield scrapy.Request(
                self.base_url.format(uf=state),
                meta={"state": state, "handle_httpstatus_all": True},
                callback=self.parse_state_file,
            )

    def parse_boletim(self, state, data):
        self.logger.info(f"Parsing {state} boletim")
        try:
            reports = rows.import_from_dicts(
                data,
                force_types={
                    "date": rows.fields.DateField,
                    "notes": rows.fields.TextField,
                    "state": rows.fields.TextField,
                    "url": rows.fields.TextField,
                },
            )
        except Exception as exp:
            self.errors[state].append(
                ("boletim", state, f"{exp.__class__.__name__}: {exp}")
            )
            return
        for report in reports:
            report = report._asdict()
            self.logger.debug(report)
            self.boletim_writer.writerow(report)

    def parse_caso(self, state, data):
        self.logger.info(f"Parsing {state} caso")
        cities = defaultdict(dict)
        for caso in data:
            for key, value in caso.items():
                if key == "municipio":
                    continue
                elif key.startswith("confirmados_") or key.startswith("mortes_"):
                    try:
                        _, day, month = key.split("_")
                    except ValueError:
                        message = f"ERROR PARSING {repr(key)} - {repr(value)} - {caso}"
                        self.errors[state].append(("caso", state, message))
                        self.logger.error(message)
                        continue
                    date = f"2020-{int(month):02d}-{int(day):02d}"
                    if key.startswith("confirmados_"):
                        number_type = "confirmed"
                    elif key.startswith("mortes_"):
                        number_type = "deaths"
                else:
                    continue
                if date not in cities[caso["municipio"]]:
                    cities[caso["municipio"]][date] = {}
                if value in (None, ""):
                    value = None
                else:
                    value = str(value)
                    if value.endswith(".0"):
                        value = value[:-2]
                    if value.startswith("=") and value[1:].isdigit():
                        value = value[1:]
                    try:
                        value = int(value)
                    except ValueError:
                        message = f"ERROR converting to int: {date} {number_type} {value} {caso}"
                        self.errors[state].append(("caso", state, message))
                        self.logger.error(message)
                        continue
                cities[caso["municipio"]][date][number_type] = value
        result = []
        for city, city_data in cities.items():
            for date, date_data in city_data.items():
                confirmed = date_data["confirmed"]
                deaths = date_data["deaths"]
                if confirmed is None and deaths is None:
                    continue
                confirmed = int(confirmed) if confirmed is not None else None
                deaths = int(deaths) if deaths is not None else None
                row = {
                    "date": date,
                    "state": state,
                    "city": city if city != "TOTAL NO ESTADO" else "",
                    "place_type": "city" if city != "TOTAL NO ESTADO" else "state",
                    "confirmed": confirmed,
                    "deaths": deaths,
                }
                confirmed = row["confirmed"]
                deaths = row["deaths"]
                NULL = (None, "")
                if (confirmed in NULL and deaths not in NULL) or (
                    deaths in NULL and confirmed not in NULL
                ):
                    message = (
                        f"ERROR: only one field is filled for {date}, {state}, {city}"
                    )
                    self.errors[state].append(("caso", state, message))
                result.append(row)

        row_key = lambda row: (row["state"], row["city"], row["place_type"])
        result.sort(key=row_key)
        groups = groupby(result, key=row_key)
        for key, row_list_it in groups:
            row_list = list(row_list_it)
            row_list.sort(key=lambda row: row["date"])
            for order_for_place, row in enumerate(row_list, start=1):
                row["order_for_place"] = order_for_place
                row["is_last"] = False
            if row_list:
                row_list[-1]["is_last"] = True

        for row in result:
            if row["place_type"] == "city":
                if row["city"] == "Importados/Indefinidos":
                    row_population_2020 = row_population_2019 = None
                    row_city_code = None
                else:
                    row_city_code = demographics.city_code(row["state"], row["city"])
                    row_population_2019 = demographics.city_population(row["state"], row["city"], year=2019)
                    row_population_2020 = demographics.city_population(row["state"], row["city"], year=2020)
            elif row["place_type"] == "state":
                row_city_code = demographics.state_code(row["state"])
                row_population_2019 = demographics.state_population(row["state"], year=2019)
                row_population_2020 = demographics.state_population(row["state"], year=2020)
            else:
                message = f"Invalid row: {row}"
                self.errors[state].append(("caso", state, message))
                self.logger.error(message)
                continue
            row_deaths = row["deaths"]
            row_confirmed = row["confirmed"]
            confirmed_per_100k = (
                100_000 * (row_confirmed / row_population_2020) if row_confirmed and row_population_2020 else None
            )
            death_rate = row_deaths / row_confirmed if row_deaths is not None and row_confirmed not in (None, 0) else 0
            row["estimated_population_2019"] = row_population_2019
            row["estimated_population"] = row_population_2020
            row["city_ibge_code"] = row_city_code
            row["confirmed_per_100k_inhabitants"] = f"{confirmed_per_100k:.5f}" if confirmed_per_100k else None
            row["death_rate"] = f"{death_rate:.4f}"
            self.logger.debug(row)
            self.caso_writer.writerow(row)

    def parse_state_file(self, response):
        state = response.meta["state"]
        if response.status >= 400:
            self.errors[state].append(
                ("connection", state, f"HTTP status code: {response.status}")
            )
        else:
            response_data = json.load(io.BytesIO(response.body))
            try:
                self.parse_boletim(state, response_data["reports"])
            except Exception as exp:
                self.errors[state].append(
                    ("boletim", state, f"{exp.__class__.__name__}: {exp}")
                )
            try:
                self.parse_caso(state, response_data["cases"])
            except Exception as exp:
                self.errors[state].append(
                    ("caso", state, f"{exp.__class__.__name__}: {exp}")
                )

        if self.errors[state]:
            error_counter = Counter(error[0] for error in self.errors[state])
            error_counter_str = ", ".join(
                f"{error_type}: {count}" for error_type, count in error_counter.items()
            )
            self.logger.error(
                f"{len(self.errors[state])} errors found when parsing {state} ({error_counter_str})"
            )
            error_header = ("sheet", "state", "message")
            errors = rows.import_from_dicts(
                [dict(zip(error_header, row)) for row in self.errors[state]]
            )
            filename = ERROR_PATH / f"errors-{state}.csv"
            if not filename.parent.exists():
                filename.parent.mkdir(parents=True)
            rows.export_to_csv(errors, filename)

    def __del__(self):
        self.boletim_writer.close()
        self.caso_writer.close()

        state_errors = [errors for errors in self.errors.values() if errors]
        if state_errors:
            # Force crawler to stop
            os.kill(os.getpid(), SIGINT)
            os.kill(os.getpid(), SIGINT)
            raise CloseSpider(f"Error found on {len(state_errors)} state(s).")
