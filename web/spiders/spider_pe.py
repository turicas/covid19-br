import datetime
import io
import json
from itertools import groupby

import rows
from cached_property import cached_property

from .base import BaseCovid19Spider


class Covid19PESpider(BaseCovid19Spider):
    name = "PE"
    start_urls = ["https://dados.seplag.pe.gov.br/apps/corona_dados.html"]

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
        page_jsons = response.xpath("//script[@type='application/json' and @data-for]/text()")
        case_data = None
        for json_data in page_jsons.extract():
            data = json.loads(json_data)["x"]
            if data['options'].get('buttons'):
                continue
            case_data = data["data"]
            break
        header = rows.import_from_html(
            io.BytesIO(data["container"].encode("utf-8"))
        ).field_names
        result = []
        for row in zip(*case_data):
            row = dict(zip(header, row))
            new = self.fix_row(row)
            if new:  # TODO: remove
                result.append(new)

        last_date = max(row["dt_notificacao"] or "" for row in result)
        year, month, day = last_date.split("-")
        self.add_report(
            date=datetime.date(int(year), int(month), int(day)),
            url=self.start_urls[0],  # TODO: should add PDF/PPT report URL?
        )

        row_key = lambda row: str(row["cd_municipio"])
        result.sort(key=row_key)
        total_confirmed = total_deaths = 0
        for city_ibge_code, city_data in groupby(result, key=row_key):
            city_ibge_code = int(city_ibge_code) if city_ibge_code else None
            city_data = [row for row in city_data if row["classe"] == "CONFIRMADO"]
            confirmed = len(city_data)
            deaths = sum(1 for row in city_data if row["evolucao"] == "ÓBITO")
            self.add_city_case(
                city=self.get_city_name_from_id(city_ibge_code),
                confirmed=confirmed,
                deaths=deaths,
            )
            total_confirmed += confirmed
            total_deaths += deaths
        self.add_state_case(confirmed=total_confirmed, deaths=total_deaths)

    def fix_row(self, row):
        new = row.copy()
        cd_municipio = new["cd_municipio"]
        if cd_municipio == '-':
            cd_municipio = 0

        if int(cd_municipio) == 0 or not new["cd_municipio"]:
            municipio = new["municipio"]
            if municipio.upper() in ("OUTRO ESTADO", "OUTRO PAÍS", "OUTRO PAIS"):
                new["cd_municipio"] = 0
            else:
                if municipio.endswith("GUA PRETA"):
                    municipio = "Água Preta"
                elif not municipio:
                    municipio = "Importados/Indefinidos"
                else:
                    try:
                        municipio.encode("iso-8859-1").decode("utf-8")
                    except UnicodeDecodeError:
                        print("ERROR", repr(municipio))
                        return {}

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
                    self.logger.error(f"Error converting city in PE: {municipio}")
                    municipio = "Importados/Indefinidos"
                new["mun_notificacao"] = municipio
                new["cd_municipio"] = self.get_city_id_from_name(municipio)
        return new
