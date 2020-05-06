import datetime
import json
from urllib.parse import urlencode, urljoin

import scrapy

import date_utils


class CearaSpider(scrapy.Spider):
    name = "CE"
    base_url = "https://indicadores.integrasus.saude.ce.gov.br/api/coronavirus/"
    start_date = datetime.date(2020, 3, 2)

    def make_state_confirmed_request(self, date, callback, meta=None):
        data = {
            "data": date,
            "idMunicipio": "",
            "tipo": "Confirmado",
        }
        url = urljoin(self.base_url, "qtd-por-municipio") + "?" + urlencode(data)
        return scrapy.Request(url, callback=callback, meta=meta)

    def make_city_deaths_request(self, date, city_id, callback, meta=None):
        data = {
            "data": date,
            "idMunicipio": city_id,
            "tipo": "Confirmado",
        }
        url = urljoin(self.base_url, "qtd-obitos") + "?" + urlencode(data)
        return scrapy.Request(url, callback=callback, meta=meta)

    def start_requests(self):
        for date in date_utils.date_range(self.start_date, date_utils.today()):
            yield self.make_state_confirmed_request(
                date, callback=self.parse_state_confirmed, meta={"row": {"date": date}},
            )

    def parse_state_confirmed(self, response):
        date = response.meta["row"]["date"]
        confirmed_data = json.loads(response.body)

        for city_data in confirmed_data:
            assert city_data["tipo"] == "Positivo"
            city = city_data["municipio"]
            if city == "Sem informação":
                city = "Importados/Indefinidos"
                city_id = None
            else:
                city_id = city_data["idMunicipio"]
            confirmed = city_data["quantidade"]
            yield self.make_city_deaths_request(
                date,
                city_id,
                callback=self.parse_city_deaths,
                meta={"row": {"date": date, "city": city, "confirmed": confirmed}},
            )
        # TODO: check if all requests made here were received as reponses

    def parse_city_deaths(self, response):
        row_data = response.meta["row"]
        row_data["state"] = self.name
        deaths_data = json.loads(response.body)

        assert len(deaths_data) == 1
        assert deaths_data[0]["tipo"] == "Óbito"
        row_data["deaths"] = deaths_data[0]["quantidade"]
        yield row_data
