import io
from datetime import datetime
from collections import defaultdict

import rows

from .base import BaseCovid19Spider


class Covid19CESpider(BaseCovid19Spider):
    name = "CE"
    start_urls = ["https://indicadores.integrasus.saude.ce.gov.br/api/coronavirus/qtd-por-municipio?tipo=Óbito,Confirmado"]

    def parse(self, response):
        encoding = "utf-8"
        table = rows.import_from_json(
            io.BytesIO(response.body),
            encoding=encoding
        )

        # TODO - get last_date from another source at *.saude.ce.gov.br
        last_date = datetime.now().date()
        self.add_report(date=last_date, url=self.start_urls[0])

        total_confirmed = total_deaths = 0
        imported_confirmed = imported_deaths = 0

        cases = defaultdict(dict)
        for row in table:

            if row.tipo == 'Confirmado':
                cases[row.municipio]["confirmed"] = row.quantidade
            elif row.tipo == 'Óbito':
                cases[row.municipio]["deaths"] = row.quantidade
            else:
                raise ValueError(f'Unknown case type : "{row.tipo}"')

        for city, city_data in cases.items():
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
