import json
from urllib.parse import urlencode, urljoin

import scrapy
from epiweeks import Week

import date_utils


class DeathsSpider(scrapy.Spider):
    name = "obitos_registral_cities"
    cities_url = "https://transparencia.registrocivil.org.br/api/covid-cities"
    registral_url = (
        "https://transparencia.registrocivil.org.br/api/covid-covid-registral"
    )

    causes_map = {
        "sars": "SRAG",
        "pneumonia": "PNEUMONIA",
        "respiratory_failure": "INSUFICIENCIA_RESPIRATORIA",
        "septicemia": "SEPTICEMIA",
        "indeterminate": "INDETERMINADA",
        "others": "OUTRAS",
    }

    def make_cities_request(self, total, callback, dont_cache=False):
        data = {
            "total": total,  # Seems not to be working, it's always 100
            "type": "registral-covid",
        }
        return scrapy.Request(
            url=urljoin(self.cities_url, "?" + urlencode(data)),
            callback=callback,
            meta={"row": data, "dont_cache": dont_cache},
        )

    def make_registral_request(
        self, city, ep_week, callback, dont_cache=False,
    ):
        data = {
            "city_id": city["city_id"],
            "state": city["uf"],
            "start_date": str(ep_week.startdate()),
            "end_date": str(ep_week.enddate()),
        }
        return scrapy.Request(
            url=urljoin(self.registral_url, "?" + urlencode(data)),
            callback=callback,
            meta={
                "row": data,
                "city_name": city["nome"],
                "ep_week": ep_week,
                "dont_cache": dont_cache,
            },
        )

    def start_requests(self):
        yield self.make_cities_request(
            total=100, callback=self.parse_cities_request, dont_cache=False
        )

    def parse_cities_request(self, response):
        cities = json.loads(response.body)

        today = date_utils.today()
        current_week = Week.fromdate(today)

        # We have to do different passes for 2019 and 2020, since the specific days of
        # the epidemiological week differs.
        #
        # The api seems to return the data from the current year as "2020", and the previous as "2019",
        # so we'll exploit that to extract the data only from the "2020" chart

        for city in cities:
            for year in [2020, 2019]:
                for weeknum in range(1, current_week.week):
                    ep_week = Week(year, weeknum)

                    # Cache more than 4 weeks ago
                    should_cache = (current_week.week - weeknum) > 4
                    yield self.make_registral_request(
                        city=city,
                        ep_week=ep_week,
                        callback=self.parse_registral_request,
                        dont_cache=not should_cache,
                    )

    def add_causes(self, row, data):
        for cause, portuguese_name in self.causes_map.items():
            row[cause] = data[portuguese_name]

    def parse_registral_request(self, response):
        ep_week = response.meta["ep_week"]

        row = response.meta["row"].copy()
        row["city_name"] = response.meta["city_name"]
        row["epidemiological_year"] = ep_week.year
        row["epidemiological_week"] = ep_week.week

        data = json.loads(response.body)

        if "dont_cache" in row:
            del row["dont_cache"]

        for cause in self.causes_map:
            row[cause] = 0

        row["covid"] = 0

        chart_data = data["chart"]
        if chart_data:
            if "2020" in chart_data:
                self.add_causes(row, chart_data["2020"])
                row["covid"] = chart_data["2020"]["COVID"]

        yield row
