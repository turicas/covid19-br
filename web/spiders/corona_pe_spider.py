import datetime
import io
import json
from itertools import groupby
from pathlib import Path
from urllib.request import urlopen

import rows
import scrapy


BASE_PATH = Path(__file__).parent.parent.parent
POPULATION_PATH = BASE_PATH / "data" / "populacao-estimada-2019.csv"
population_pe = [
    row
    for row in rows.import_from_csv(POPULATION_PATH)
    if row.state == "PE"
]
CITY_NAME_BY_ID = {
    int(str(row.city_ibge_code)[:-1]): row.city
    for row in population_pe
}
CITY_NAME_BY_ID[0] = "Importados/Indefinidos"
CITY_NAME_BY_SLUG = {
    rows.fields.slug(row.city): row.city
    for row in population_pe
}
CITY_NAME_BY_SLUG[rows.fields.slug("Importados/Indefinidos")] = "Importados/Indefinidos"
CITY_ID_BY_NAME = {
    row.city: int(str(row.city_ibge_code)[:-1])
    for row in rows.import_from_csv(POPULATION_PATH)
    if row.state == "PE"
}
CITY_ID_BY_NAME["Importados/Indefinidos"] = 0


def fix_row(row):
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
                municipio = municipio.encode("iso-8859-1").decode("utf-8").title().replace(" Do ", " do ").replace(" Da ", " da ").replace(" De ", " de ")
            try:
                municipio = CITY_NAME_BY_SLUG[rows.fields.slug(municipio)]
            except KeyError:
                print(f"Error converting city in PE: {municipio}")
                municipio = "Importados/Indefinidos"
            new["mun_notificacao"] = municipio
            new["cd_municipio"] = CITY_ID_BY_NAME[municipio]

    return new


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
            result.append(fix_row(row))

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
                "municipio": CITY_NAME_BY_ID[city_ibge_code],
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
