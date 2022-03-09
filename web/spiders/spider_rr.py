import datetime
import io

import rows

from .base import BaseCovid19Spider


class Covid19RRSpider(BaseCovid19Spider):
    name = "RR"
    start_urls = ["https://roraimacontraocorona.rr.gov.br/winner/public/mapa.xhtml"]

    def parse(self, response):
        date = response.body_as_unicode().split("Atualizado em")[1].split()[0]
        day, month, year = date.split("/")
        self.add_report(
            date=datetime.date(int(year), int(month), int(day)), url=self.start_urls[0]
        )

        table = rows.import_from_html(
            io.BytesIO(response.body), encoding=response.encoding
        )
        for row in table:
            if (row.confirmados, row.obitos) == (None, None):
                continue
            city_name = row.cidade
            confirmed = row.confirmados
            deaths = row.obitos or 0
            if city_name.lower().strip() == "total:":
                self.add_state_case(confirmed=confirmed, deaths=deaths)
            else:
                self.add_city_case(city=city_name, confirmed=confirmed, deaths=deaths)
        self.add_city_case(city="Importados/Indefinidos", confirmed=None, deaths=None)
        # TODO: is there any way to get Importados/Indefinidos?
