import datetime
import io
import json
from itertools import groupby
from pathlib import Path
from urllib.request import urlopen

import rows
import scrapy


BASE_PATH = Path(__file__).parent
POPULATION_PATH = BASE_PATH / "data" / "populacao-estimada-2019.csv"
PE_CITIES = {
    int(str(row.city_ibge_code)[:-1]): row.city
    for row in rows.import_from_csv(POPULATION_PATH)
    if row.state == "PE"
}
PE_CITIES[0] = "Importados/Indefinidos"


class Covid19PESpider(scrapy.Spider):
    name = "pe"
    start_urls = ["https://dados.seplag.pe.gov.br/apps/corona.html#dados-pe"]

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
            result.append(row)

        now = datetime.datetime.now()
        date = datetime.date(now.year, now.month, now.day)
        row_key = lambda row: row["cd_municipio"]
        result.sort(key=row_key)
        total_confirmed = total_deaths = 0
        for city_ibge_code, city_data in groupby(result, key=row_key):
            city_data = [row for row in city_data if row["classe"] == "CONFIRMADO"]
            confirmed = len(city_data)
            deaths = sum(1 for row in city_data if row["evolucao"] == "ÓBITO")
            row = {
                "municipio": PE_CITIES[city_ibge_code],
                "confirmados": confirmed,
                "mortes": deaths,
            }
            total_confirmed += confirmed
            total_deaths += deaths
            yield row
        yield {
            "municipio": "TOTAL NO ESTADO",
            "confirmados": total_confirmed,
            "mortes": total_deaths,
        }
