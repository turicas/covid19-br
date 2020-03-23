import csv
import io
from collections import defaultdict
from urllib.parse import parse_qs, urlparse

import rows
import scrapy


def gdocs_xlsx_download_url(url):
    spreadsheet_id = parse_qs(urlparse(url).query)["id"][0]
    return f"https://docs.google.com/spreadsheets/u/0/d/{spreadsheet_id}/export?format=xlsx&id={spreadsheet_id}"


class ConsolidaSpider(scrapy.Spider):
    name = "consolida"
    start_urls = ["https://docs.google.com/spreadsheets/u/0/d/1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI/export?format=csv&id=1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI&gid=0"]

    def __init__(self, boletim_filename, caso_filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boletim_writer = rows.utils.CsvLazyDictWriter(boletim_filename)
        self.caso_writer = rows.utils.CsvLazyDictWriter(caso_filename)

    def parse(self, response):
        table = rows.import_from_csv(
            io.BytesIO(response.body), encoding="utf-8"
        )
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
        casos = rows.import_from_xlsx(io.BytesIO(response.body), sheet_name="Casos (FINAL)")
        cities = defaultdict(dict)
        for caso in casos:
            caso = caso._asdict()
            caso_data = [item for item in caso.values() if item]
            if not caso_data:
                continue
            elif not caso["municipio"].strip():
                if not caso[key]:
                    continue
                else:
                    self.logger.warning(f"ERROR PARSING (empty city) {caso}")
            for key, value in caso.items():
                if key == "municipio":
                    continue
                if key.startswith("confirmados_") or key.startswith("mortes_"):
                    try:
                        _, day, month = key.split("_")
                    except ValueError:
                        self.logger.error(f"ERROR PARSING {repr(key)} - {repr(value)} - {caso}")
                        continue
                    date = f"2020-{int(month):02d}-{int(day):02d}"
                    if key.startswith("confirmados_"):
                        number_type = "confirmed"
                    elif key.startswith("mortes_"):
                        number_type = "deaths"
                else:
                    self.logger.error(f"ERROR PARSING {caso}")
                if date not in cities[caso["municipio"]]:
                    cities[caso["municipio"]][date] = {}
                try:
                    value = int(value) if value else ""
                except ValueError:
                    self.logger.error(f"ERROR converting to int: {date} {number_type} {value} {caso}")
                    continue
                cities[caso["municipio"]][date][number_type] = value
        for city, city_data in cities.items():
            for date, date_data in city_data.items():
                confirmed = date_data["confirmed"]
                deaths = date_data["deaths"]
                if not confirmed and not deaths:
                    continue
                row = {
                    "date": date,
                    "state": state,
                    "city": city if city != "TOTAL NO ESTADO" else "",
                    "place_type": "city" if city != "TOTAL NO ESTADO" else "state",
                    "confirmed": confirmed,
                    "deaths": deaths,
                }
                self.logger.debug(row)
                self.caso_writer.writerow(row)

    def __del__(self):
        self.boletim_writer.close()
        self.caso_writer.close()
