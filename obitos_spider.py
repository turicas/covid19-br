import datetime
import json
from urllib.parse import urlencode, urljoin

import scrapy

import date_utils

STATES = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()


class DeathsSpider(scrapy.Spider):
    name = "obitos"
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

    def make_registral_request(
        self, start_date, end_date, state, callback, dont_cache=False
    ):
        data = {
            "state": state,
            "start_date": str(start_date),
            "end_date": str(end_date),
        }
        return scrapy.Request(
            url=urljoin(self.registral_url, "?" + urlencode(data)),
            callback=callback,
            meta={"row": data, "dont_cache": dont_cache},
        )

    def start_requests(self):
        today = date_utils.today()
        tomorrow = today + datetime.timedelta(days=1)
        # `date_utils.date_range` excludes the last, so to get today's data we
        # need to pass tomorrow.
        for date in date_utils.date_range(datetime.date(2020, 1, 1), tomorrow):
            # Won't cache dates from 30 days ago until today (only historical
            # ones which are unlikely to change).
            should_cache = today - date > datetime.timedelta(days=30)
            for state in STATES:
                yield self.make_registral_request(
                    start_date=date,
                    end_date=date,
                    state=state,
                    callback=self.parse_registral_request,
                    dont_cache=not should_cache,
                )

    def add_causes(self, row, data, year):
        for cause, portuguese_name in self.causes_map.items():
            row[cause + "_" + year] = data[portuguese_name]

    def parse_registral_request(self, response):
        row = response.meta["row"].copy()
        data = json.loads(response.body)
        assert row["start_date"] == row.pop("end_date")
        row["date"] = row.pop("start_date")
        year, month, day = row["date"].split("-")
        date = datetime.date(int(year), int(month), int(day))
        if "dont_cache" in row:
            del row["dont_cache"]

        for year in ["2019", "2020"]:
            for cause in self.causes_map:
                row[cause + "_" + year] = 0

        row["covid"] = 0

        chart_data = data["chart"]
        if chart_data:
            if "2019" in chart_data and "2020" in chart_data:
                try:
                    datetime.date(2019, date.month, date.day)
                except ValueError:
                    # This day does not exist on 2019 and the API returned
                    # 2019's next day data.
                    pass
                else:
                    self.add_causes(row, chart_data["2019"], "2019")

                self.add_causes(row, chart_data["2020"], "2020")
                row["covid"] = chart_data["2020"]["COVID"]

        yield row
