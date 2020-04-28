import datetime
import io
import json
from itertools import groupby

import rows
from cached_property import cached_property

from .base import BaseCovid19Spider


class Covid19PESpider(BaseCovid19Spider):
    name = "PE"
    start_urls = ["https://dados.seplag.pe.gov.br/apps/corona.html#dados-pe"]

    @cached_property
    def city_name_from_id(self):
        data = {int(str(row.city_ibge_code)[:-1]): row.city for row in self.population}
        data[0] = "Importados/Indefinidos"
        return data

    @cached_property
    def city_id_from_name(self):
        data = {row.city: int(str(row.city_ibge_code)[:-1]) for row in self.population}
        data["Importados/Indefinidos"] = 0
        return data

    def parse(self, response):
        page_jsons = response.xpath("//script[@type = 'application/json']/text()")
        case_data = None
        for json_data in page_jsons.extract():
            data = json.loads(json_data)["x"]
            if (
                "csv" not in data["options"].get("buttons", [])
                or "mun_notificacao" not in data["container"]
            ):
                continue
            case_data = data["data"]
            break
        header = rows.import_from_html(
            io.BytesIO(data["container"].encode("utf-8"))
        ).field_names
        result = []
        for row in zip(*case_data):
            row = dict(zip(header, row))
            result.append(self.fix_row(row))

        now = datetime.datetime.now()
        date = datetime.date(now.year, now.month, now.day)
        row_key = lambda row: str(row["cd_municipio"])
        result.sort(key=row_key)
        total_confirmed = total_deaths = 0
        for city_ibge_code, city_data in groupby(result, key=row_key):
            city_ibge_code = int(city_ibge_code) if city_ibge_code else None
            city_data = [row for row in city_data if row["classe"] == "CONFIRMADO"]
            confirmed = len(city_data)
            deaths = sum(1 for row in city_data if row["evolucao"] == "ÓBITO")
            row = {
                "municipio": self.get_city_name_from_id(city_ibge_code),
                "confirmados": confirmed,
                "mortes": deaths,
            }
            total_confirmed += confirmed
            total_deaths += deaths
            self.write_row(row)
        self.write_row(
            {
                "municipio": "TOTAL NO ESTADO",
                "confirmados": total_confirmed,
                "mortes": total_deaths,
            }
        )

    def fix_row(self, row):
        new = row.copy()
        if int(new["cd_municipio"]) == 0 or not new["cd_municipio"]:
            municipio = new["mun_notificacao"]
            if municipio in ("OUTRO ESTADO", "OUTRO PAÍS"):
                new["cd_municipio"] = 0
            else:
                if municipio.endswith("GUA PRETA"):
                    municipio = "Água Preta"
                elif not municipio:
                    municipio = "Importados/Indefinidos"
                else:
                    municipio = (
                        municipio.encode("iso-8859-1")
                        .decode("utf-8")
                        .title()
                        .replace(" Do ", " do ")
                        .replace(" Da ", " da ")
                        .replace(" De ", " de ")
                    )
                try:
                    # Get correct city name
                    city_id = self.get_city_id_from_name(municipio)
                    municipio = self.get_city_name_from_id(city_id)
                except KeyError:
                    print(f"Error converting city in PE: {municipio}")
                    municipio = "Importados/Indefinidos"
                new["mun_notificacao"] = municipio
                new["cd_municipio"] = self.get_city_id_from_name(municipio)
        return new
