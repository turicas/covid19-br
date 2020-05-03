import datetime
import json
from urllib.parse import urlencode, urljoin
from epiweeks import Week, Year

import scrapy

import date_utils


STATES = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()


class DeathsSpider(scrapy.Spider):
    name = "obitos_registral_cities"
    cities_url = "https://transparencia.registrocivil.org.br/api/covid-cities" # ?total=100&type=registral-covid
    registral_url = "https://transparencia.registrocivil.org.br/api/covid-covid-registral"

    causes_map = {
        "sars": "SRAG",
        "pneumonia": "PNEUMONIA",
        "respiratory_failure": "INSUFICIENCIA_RESPIRATORIA",
        "septicemia": "SEPTICEMIA",
        "indeterminate": "INDETERMINADA",
        "others": "OUTRAS"
    }

    def make_cities_request(
        self,
        total,
        callback,
        dont_cache=False
    ):
        data = {
            "total": total,
            "type": "registral-covid"
        }
        return scrapy.Request(
            url=urljoin(self.cities_url, "?" + urlencode(data)),
            callback=callback,
            meta={"row": data, "dont_cache": dont_cache},
        )

    def make_registral_request(
        self,
        start_date,
        end_date,
        city,
        callback,
        dont_cache=False,
    ):
        data = {
            "city_id": city["city_id"],
            "state": city["uf"],
            "start_date": str(start_date),
            "end_date": str(end_date),
        }
        return scrapy.Request(
            url=urljoin(self.registral_url, "?" + urlencode(data)),
            callback=callback,
            meta={"row": data, "city_name": city["nome"], "dont_cache": dont_cache},
        )

    def start_requests(self):
        yield self.make_cities_request(
            total=100,
            callback=self.parse_cities_request,
            dont_cache=False
        )

    def parse_cities_request(self, response):
        row = response.meta["row"].copy()
        cities = json.loads(response.body)

        today = date_utils.today()

        for city in cities:
            for week in Year(2020).iterweeks():
                if week.startdate() > today: 
                    break;

                # Won't cache dates from 30 days ago until today (only historical
                # ones which are unlikely to change).
                should_cache = today - week.startdate() > datetime.timedelta(days=30)
                yield self.make_registral_request(
                    start_date=week.startdate(),
                    end_date=week.enddate(),
                    city=city,
                    callback=self.parse_registral_request,
                    dont_cache=not should_cache,
                )

    def add_causes(self, row, data, year):
        for cause, portuguese_name in self.causes_map.items():
            row[cause + "_" + year] = data[portuguese_name]

    def parse_registral_request(self, response):
        row = response.meta["row"].copy()
        row["city_name"] = response.meta["city_name"]

        data = json.loads(response.body)
                
        if "dont_cache" in row:
            del row["dont_cache"]

        for year in ["2019", "2020"]:
            for cause in self.causes_map:
                row[cause + "_" + year] = 0

        row["covid"] = 0
        
        chart_data = data["chart"]
        if chart_data:
            if "2019" in chart_data and "2020" in chart_data:
                self.add_causes(row, chart_data["2019"], "2019")
                self.add_causes(row, chart_data["2020"], "2020")
                row["covid"] = chart_data["2020"]["COVID"]

        yield row
