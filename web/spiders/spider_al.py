import io
from itertools import groupby
from datetime import datetime

import rows

from .base import BaseCovid19Spider

class Covid19ALSpider(BaseCovid19Spider):
    name = "AL"
    start_urls = ["https://covid19.dados.al.gov.br/dados"]

    def parse(self, response):
        encoding = "utf-8"
        table = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding=encoding
        )
        table = [row for row in table if row.classificacao == "Confirmado"]

        # TODO - get last_date from response header Ex. : b'Content-Disposition': [b'attachment; filename=paciente10.06.2020.csv']
        last_date = datetime.now().date()
        self.add_report(date=last_date, url=self.start_urls[0])

        row_key = lambda row: row.municipio_residencia

        table.sort(key=row_key)
        total_confirmed = total_deaths = 0
        imported_confirmed = imported_deaths = None

        for city, cases in groupby(table, key=row_key):         
            cases = list(cases)
            confirmed = len(cases)
            deaths = sum(1 for row in cases if row.situacao_atual == 'Óbito')
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
