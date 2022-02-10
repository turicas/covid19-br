import io
from itertools import groupby

import rows

from .base import BaseCovid19Spider


class PtBrDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"


class Covid19ESSpider(BaseCovid19Spider):
    name = "ES"
    start_urls = ["https://bi.static.es.gov.br/covid19/MICRODADOS.csv"]

    def parse(self, response):
        encoding = "utf-8"
        table = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding=encoding,
            force_types={"data": PtBrDateField},
        )
        table = [row for row in table if row.classificacao == "Confirmados"]

        last_date = max(row.data for row in table)
        self.add_report(date=last_date, url=self.start_urls[0])

        row_key = lambda row: row.municipio
        table.sort(key=row_key)
        total_confirmed = total_deaths = 0
        imported_confirmed = imported_deaths = None
        for city, cases in groupby(table, key=row_key):
            cases = list(cases)
            confirmed = len(cases)
            deaths = sum(1 for row in cases if "óbito" in row.evolucao.lower())
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
