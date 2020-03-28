import csv
import io
from collections import Counter, defaultdict
from itertools import groupby
from urllib.parse import parse_qs, urlparse

import rows
import scrapy


def gdocs_xlsx_download_url(url):
    spreadsheet_id = parse_qs(urlparse(url).query)["id"][0]
    return f"https://docs.google.com/spreadsheets/u/0/d/{spreadsheet_id}/export?format=xlsx&id={spreadsheet_id}"


class ConsolidaSpider(scrapy.Spider):
    name = "consolida"
    start_urls = [
        "https://docs.google.com/spreadsheets/u/0/d/1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI/export?format=csv&id=1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI&gid=0"
    ]

    def __init__(self, boletim_filename, caso_filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boletim_writer = rows.utils.CsvLazyDictWriter(boletim_filename)
        self.caso_writer = rows.utils.CsvLazyDictWriter(caso_filename)

        population = rows.import_from_csv(
            "data/populacao-estimada-2019.csv",
            force_types={
                "populacao_estimada": rows.fields.IntegerField,
                "codigo_municipio": rows.fields.TextField,
            },
        )
        self.population_per_city = {
            (city.uf, city.municipio): city.populacao_estimada for city in population
        }
        self.city_code = {
            (city.uf, city.municipio): city.codigo_municipio for city in population
        }
        self.state_code = {city.uf: city.codigo_uf for city in population}
        self.population_per_state = Counter()
        for city in population:
            self.population_per_state[city.uf] += city.populacao_estimada

    def parse(self, response):
        table = rows.import_from_csv(io.BytesIO(response.body), encoding="utf-8")
        for row in table:
            yield scrapy.Request(
                gdocs_xlsx_download_url(row.planilha_brasilio),
                meta={"state": row.uf},
                callback=self.parse_state_file,
            )

    def parse_state_file(self, response):
        state = response.meta["state"]

        self.logger.info(f"Parsing {state} boletim")
        boletins = rows.import_from_xlsx(
            io.BytesIO(response.body),
            sheet_name="Boletins (FINAL)",
            force_types={
                "date": rows.fields.DateField,
                "url": rows.fields.TextField,
                "notes": rows.fields.TextField,
            },
        )
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

        self.logger.info(f"Parsing {state} caso")
        casos = rows.import_from_xlsx(
            io.BytesIO(response.body), sheet_name="Casos (FINAL)"
        )
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
                        self.logger.error(
                            f"ERROR PARSING {repr(key)} - {repr(value)} - {caso}"
                        )
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
                try:
                    value = int(value) if value not in (None, "") else None
                except ValueError:
                    self.logger.error(
                        f"ERROR converting to int: {date} {number_type} {value} {caso}"
                    )
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
            for order, row in enumerate(row_list, start=1):
                row["order"] = order
                row["is_last"] = False
            if row_list:
                row_list[-1]["is_last"] = True

        for row in result:
            if row["place_type"] == "city":
                if row["city"] == "Importados/Indefinidos":
                    row_population = None
                    row_city_code = None
                else:
                    state_code = int(self.state_code[row["state"]])
                    city_code = int(self.city_code[(row["state"], row["city"])])
                    row_population = self.population_per_city[
                        (row["state"], row["city"])
                    ]
                    row_city_code = f"{state_code:02d}{city_code:05d}"
            elif row["place_type"] == "state":
                state_code = int(self.state_code[row["state"]])
                row_population = self.population_per_state[row["state"]]
                row_city_code = f"{state_code:02d}"
            else:
                self.logger.error(f"Invalid row: {row}")
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

    def __del__(self):
        self.boletim_writer.close()
        self.caso_writer.close()
