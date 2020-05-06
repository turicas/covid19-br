import datetime
import io
from urllib.parse import urljoin

import rows
import scrapy

from .base import BaseCovid19Spider


class Covid19PRSpider(BaseCovid19Spider):
    name = "PR"
    start_urls = [
        "http://www.saude.pr.gov.br/modules/conteudo/conteudo.php?conteudo=3507"
    ]

    def parse(self, response):
        url = response.xpath("//a[contains(@href, '.csv')]/@href")[0].extract()
        full_url = urljoin(response.url, url)
        day, month, year = (
            rows.fields.slug(full_url)
            .split("epidemiologico_")[1]
            .split("_csv")[0]
            .split("_")
        )
        date = datetime.date(int(year), int(month), int(day))
        self.add_report(date=date, url=full_url)
        yield scrapy.Request(
            url=full_url, meta={"row": {"date": date}}, callback=self.parse_csv
        )

    def parse_csv(self, response):
        table = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding=response.encoding,
            force_types={
                "confirmados": rows.fields.IntegerField,
                "obitos": rows.fields.IntegerField,
            },
        )
        total_confirmed = total_deaths = 0
        for row in table:
            if row.obitos is None and row.confirmados is None:
                continue
            city = row.municipio
            deaths = row.obitos or 0
            confirmed = row.confirmados or 0
            self.add_city_case(city=city, confirmed=confirmed, deaths=deaths)
            total_confirmed += confirmed
            total_deaths += deaths
        # TODO: check if we can get values for "Importados/Indefinidos"
        self.add_city_case(city="Importados/Indefinidos", confirmed=None, deaths=None)
        self.add_state_case(confirmed=total_confirmed, deaths=total_deaths)
