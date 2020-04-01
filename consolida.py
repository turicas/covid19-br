import csv
import io
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import groupby
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import rows
import scrapy
from cached_property import cached_property
from rows.utils import load_schema


DATA_PATH = Path(__file__).parent / "data"
SCHEMA_PATH = Path(__file__).parent / "schema"
POPULATION_DATA_PATH = DATA_PATH / "populacao-estimada-2019.csv"
POPULATION_SCHEMA_PATH = SCHEMA_PATH / "populacao-estimada-2019.csv"
STATE_LINKS_SPREADSHEET_ID = "1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI"


@lru_cache()
def get_cities():
    table = rows.import_from_csv(
        POPULATION_DATA_PATH, force_types=load_schema(str(POPULATION_SCHEMA_PATH)),
    )
    cities = defaultdict(dict)
    for row in table:
        cities[row.uf][row.municipio] = row
    return cities


@lru_cache()
def get_city_code(state, city):
    return int(get_cities()[state][city].codigo_municipio)


@lru_cache()
def get_city_population(state, city):
    return get_cities()[state][city].populacao_estimada


@lru_cache()
def get_state_code(state):
    for city in get_cities()[state].values():
        return int(city.codigo_uf)


@lru_cache()
def get_state_population(state):
    return sum(city.populacao_estimada for city in get_cities()[state].values())


def spreadsheet_download_url(url_or_id, file_format):
    if url_or_id.startswith("http"):
        spreadsheet_id = parse_qs(urlparse(url_or_id).query)["id"][0]
    else:
        spreadsheet_id = url_or_id
    return f"https://docs.google.com/spreadsheets/u/0/d/{spreadsheet_id}/export?format={file_format}&id={spreadsheet_id}"


class ConsolidaSpider(scrapy.Spider):
    name = "consolida"
    start_urls = [spreadsheet_download_url(STATE_LINKS_SPREADSHEET_ID, "csv")]

    def __init__(self, boletim_filename, caso_filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boletim_writer = rows.utils.CsvLazyDictWriter(boletim_filename)
        self.caso_writer = rows.utils.CsvLazyDictWriter(caso_filename)

    def parse(self, response):
        table = rows.import_from_csv(io.BytesIO(response.body), encoding="utf-8")
        for row in table:
            yield scrapy.Request(
                spreadsheet_download_url(row.planilha_brasilio, "xlsx"),
                meta={"state": row.uf},
                callback=self.parse_state_file,
            )

    def parse_boletim(self, state, data):
        self.logger.info(f"Parsing {state} boletim")
        try:
            boletins = rows.import_from_xlsx(
                io.BytesIO(data),
                sheet_name="Boletins (FINAL)",
                force_types={
                    "date": rows.fields.DateField,
                    "url": rows.fields.TextField,
                    "notes": rows.fields.TextField,
                },
            )
        except Exception as exp:
            self.errors.append(("boletim", state, f"{exp.__class__.__name__}: {exp}"))
            return
        for boletim in boletins:
            boletim = boletim._asdict()
            boletim_data = [item for item in boletim.values() if item]
            if not boletim_data:
                continue
            boletim = {
                "date": boletim["date"],
                "state": state,
                "url": boletim["url"],
                "notes": boletim["notes"],
            }
            self.logger.debug(boletim)
            self.boletim_writer.writerow(boletim)

    def parse_caso(self, state, data):
        self.logger.info(f"Parsing {state} caso")
        casos = rows.import_from_xlsx(io.BytesIO(data), sheet_name="Casos (FINAL)")
        cities = defaultdict(dict)
        for caso in casos:
            caso = caso._asdict()
            caso_data = [
                value
                for key, value in caso.items()
                if key != "municipio" and value is not None
            ]
            if not caso_data:
                continue
            for key, value in caso.items():
                if key == "municipio":
                    continue
                elif key.startswith("confirmados_") or key.startswith("mortes_"):
                    try:
                        _, day, month = key.split("_")
                    except ValueError:
                        message = f"ERROR PARSING {repr(key)} - {repr(value)} - {caso}"
                        self.errors.append(("caso", state, message))
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
                        self.errors.append(("caso", state, message))
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
                    row_population = None
                    row_city_code = None
                else:
                    state_code = get_state_code(row["state"])
                    city_code = get_city_code(row["state"], row["city"])
                    row_population = get_city_population(row["state"], row["city"])
                    row_city_code = f"{state_code:02d}{city_code:05d}"
            elif row["place_type"] == "state":
                state_code = get_state_code(row["state"])
                row_population = get_state_population(row["state"])
                row_city_code = f"{state_code:02d}"
            else:
                message = f"Invalid row: {row}"
                self.errors.append(("caso", state, message))
                self.logger.error(message)
                continue
            row_deaths = row["deaths"]
            row_confirmed = row["confirmed"]
            confirmed_per_100k = (
                100_000 * (row_confirmed / row_population)
                if row_confirmed and row_population
                else None
            )
            death_rate = (
                row_deaths / row_confirmed if row_deaths and row_confirmed else None
            )
            row["estimated_population_2019"] = row_population
            row["city_ibge_code"] = row_city_code
            row["confirmed_per_100k_inhabitants"] = (
                f"{confirmed_per_100k:.5f}" if confirmed_per_100k else None
            )
            row["death_rate"] = f"{death_rate:.4f}" if death_rate else None
            self.logger.debug(row)
            self.caso_writer.writerow(row)

    def parse_state_file(self, response):
        state = response.meta["state"]

        self.errors = []
        try:
            self.parse_boletim(state, response.body)
        except Exception as exp:
            self.errors.append(("boletim", state, f"{exp.__class__.__name__}: {exp}"))
        try:
            self.parse_caso(state, response.body)
        except Exception as exp:
            self.errors.append(("caso", state, f"{exp.__class__.__name__}: {exp}"))
        if self.errors:
            error_counter = Counter(error[0] for error in self.errors)
            error_counter_str = ", ".join(
                f"{error_type}: {count}" for error_type, count in error_counter.items()
            )
            self.logger.error(
                f"{len(self.errors)} errors found when parsing {state} ({error_counter_str})"
            )
            error_header = ("sheet", "state", "message")
            errors = rows.import_from_dicts(
                [dict(zip(error_header, row)) for row in self.errors]
            )
            rows.export_to_csv(errors, f"errors-{state}.csv")
            exit(255)

    def __del__(self):
        self.boletim_writer.close()
        self.caso_writer.close()
