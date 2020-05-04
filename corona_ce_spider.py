import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlencode, urljoin

import scrapy

import date_utils


class CearaSpider(scrapy.Spider):
    name = "CE"
    start_date = date(2020, 3, 2)
    base_url = "https://indicadores.integrasus.saude.ce.gov.br/api/coronavirus/"

    def make_city_request(self, date, meta):
        data = {
            "data": date,
            "tipo": "Confirmado,Óbito",
        }
        url = urljoin(self.base_url, "qtd-por-municipio") + "?" + urlencode(data)
        return scrapy.Request(url, callback=self.parse_city, meta=meta)

    def make_state_confirmed_request(self, date, meta):
        data = {
            "data": date,
            "tipo": "Confirmado",
        }
        url = urljoin(self.base_url, "qtd-por-tipo") + "?" + urlencode(data)
        return scrapy.Request(url, callback=self.parse_state_confirmed, meta=meta)

    def make_state_deaths_request(self, date, meta):
        data = {
            "data": date,
            "tipo": "Óbito",
        }
        url = urljoin(self.base_url, "qtd-obitos") + "?" + urlencode(data)
        return scrapy.Request(url, callback=self.parse_state_death, meta=meta)

    def start_requests(self):
        filtro_data_url = urljoin(self.base_url, "job")
        yield scrapy.Request(filtro_data_url, self.parse_filter_date)

    def parse_filter_date(self, response):
        filter_date = json.loads(response.body)
        date_str = filter_date["time"].split(" ")[0]
        end_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        end_date += timedelta(days=1)

        for case_date in date_utils.date_range(self.start_date, end_date):
            meta = {"date": case_date}

            yield self.make_city_request(date=case_date, meta=meta)
            yield self.make_state_confirmed_request(date=case_date, meta=meta)

    def parse_city(self, response):
        map_city_case = defaultdict(dict)
        cases = json.loads(response.body)

        for case in cases:
            municipio = case["municipio"]
            map_city_case[municipio].update(case)

        for case in map_city_case.values():
            municipio = case["municipio"]
            if municipio == "Sem informação":
                municipio = "Importados/Indefinidos"

            yield {
                "date": response.meta["date"],
                "state": self.name,
                "city": municipio.title(),
                "place_type": "city",
                "confirmed": case.get("qtdConfirmado") or None,
                "deaths": case.get("qtdObito") or None,
            }

    def parse_state_confirmed(self, response):
        meta = {"date": response.meta["date"], "confirmed": json.loads(response.body)}
        yield self.make_state_deaths_request(date=response.meta["date"], meta=meta)

    def parse_state_death(self, response):
        all_types = json.loads(response.body) + response.meta["confirmed"]
        map_type_qtt = {item["tipo"]: item["quantidade"] for item in all_types}

        yield {
            "date": response.meta["date"],
            "state": self.name,
            "city": None,
            "place_type": "state",
            "confirmed": map_type_qtt.get("Positivo"),
            "deaths": map_type_qtt.get("Óbito") or None,
        }
