import io
import json
import os
from urllib.parse import urlencode

import scrapy

from .base import BaseCovid19Spider


class Covid19PASpider(BaseCovid19Spider):
    name = "PA"
    base_url = "https://www.covid-19.pa.gov.br/monitoramento-corona-service/statuscorona/casos-confirmados-obitos-por-municipio"
    splash_url = os.environ.get("SPLASH_URL", None)

    def start_requests(self):
        qs = urlencode({"url": self.base_url})
        start_url = f"{self.splash_url}?{qs}"
        yield scrapy.Request(start_url)

    def parse(self, response):
        pass
        # TODO: get data from HTML
        # self.add_city_case(city=..., confirmed=..., deaths=...)
        # self.add_city_case(city="Importados/Indefinidos", confirmed=..., deaths=...)
        # self.add_state_case(confirmed=..., deaths=...)
