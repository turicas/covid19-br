import io
from itertools import groupby
from collections import defaultdict
from datetime import datetime

import rows

from .base import BaseCovid19Spider

class YMDDateField(rows.fields.DateField):
    INPUT_FORMAT = "%Y%m%d"


class Covid19GOSpider(BaseCovid19Spider):
    name = "GO"
    start_urls = [
        "http://datasets.saude.go.gov.br/coronavirus/obitos_confirmados.csv",
        "http://datasets.saude.go.gov.br/coronavirus/casos_confirmados.csv"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = defaultdict(dict)

    def parse(self, response):
        table = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding=response.encoding,
            force_types={"data_notificacao": YMDDateField},
        )

        table = [row for row in table]

        # FIXME : make sure the REAL last date is used, since it will differ from obitos_confirmados.csv and casos_confirmados.csv
        last_date = max(row.data_notificacao for row in table)
        self.add_report(date=last_date, url=response.url)

        row_key = lambda row: row.municipio
        table.sort(key=row_key)

        for city, city_data in groupby(table, key=row_key):
            if "casos_confirmados.csv" in response.url:
                self.cases[city]["confirmed"] = len(list(city_data))
            elif "obitos_confirmados.csv" in response.url:
                self.cases[city]["deaths"] = len(list(city_data))

    def spider_closed(self):

        total_confirmed = total_deaths = 0
        imported_confirmed = imported_deaths = 0

        for city, city_data in self.cases.items():
            confirmed = city_data["confirmed"]
            deaths = city_data.get("deaths", 0)

            try:
                self.get_city_id_from_name(city)
            except KeyError:
                imported_confirmed += confirmed
                imported_deaths += deaths
            else:
                self.add_city_case(city=city, confirmed=confirmed, deaths=deaths)

            total_confirmed += confirmed
            total_deaths += deaths

        if imported_confirmed == imported_deaths == 0:
            imported_confirmed = imported_deaths = None

        self.add_city_case(
            city="Importados/Indefinidos",
            confirmed=imported_confirmed,
            deaths=imported_deaths,
        )

        self.add_state_case(confirmed=total_confirmed, deaths=total_deaths)

        super().spider_closed(self)