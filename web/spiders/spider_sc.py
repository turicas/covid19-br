import io
from itertools import groupby
from datetime import datetime
from scrapy.http import Request

import rows

from .base import BaseCovid19Spider


class Covid19SCSpider(BaseCovid19Spider):
    name = "SC"

    def start_requests(self):
        yield Request('ftp://ftp2.ciasc.gov.br/boavista_covid_dados_abertos.csv',
                      meta={'ftp_user': 'boavista', 'ftp_password': 'dados_abertos'})

    def parse(self, response):
        encoding = "utf-8"
        table = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding=encoding
        )

        table = [row for row in table if row.classificacao == "CONFIRMADO"]

        last_date = table[0].data_publicacao
        self.add_report(date=last_date, url="http://dados.sc.gov.br/dataset/covid-19-dados-anonimizados-de-casos-confirmados/resource/76d6dfe8-7fe9-45c1-95f4-cab971803d49")

        row_key = lambda row: row.municipio

        table.sort(key=row_key)
        total_confirmed = total_deaths = 0
        imported_confirmed = imported_deaths = None

        for city, cases in groupby(table, key=row_key):
            cases = list(cases)
            confirmed = len(cases)
            deaths = sum(1 for row in cases if row.obito == 'SIM')
            try:
                self.get_city_id_from_name(city)
            except KeyError:
                imported_confirmed = (imported_confirmed or 0) + confirmed
                imported_deaths = (imported_deaths or 0) + deaths
            else:
                self.add_city_case(city=city, confirmed=confirmed, deaths=deaths)
            total_confirmed += confirmed
            total_deaths += deaths
        self.add_city_case(
            city="Importados/Indefinidos",
            confirmed=imported_confirmed,
            deaths=imported_deaths,
        )
        self.add_state_case(confirmed=total_confirmed, deaths=total_deaths)