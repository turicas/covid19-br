import datetime
import json
from urllib.parse import urlencode, urljoin

import scrapy

import date_utils


STATES = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()


class DeathsSpider(scrapy.Spider):
    name = "obitos"
    deaths_url = "https://transparencia.registrocivil.org.br/api/record/death"
    covid_url = "https://transparencia.registrocivil.org.br/api/covid"

    def make_deaths_request(self, start_date, end_date, callback):
        data = {
            "start_date": str(start_date),
            "end_date": str(end_date),
        }
        return scrapy.Request(
            url=urljoin(self.deaths_url, "?" + urlencode(data)), callback=callback,
        )

    def make_covid_request(
        self,
        start_date,
        end_date,
        date_type,
        search,
        cause,
        state,
        callback,
        dont_cache=False,
    ):
        assert date_type in ("data_ocorrido", "data_registro")
        assert search in ("death-respiratory", "death-covid")
        assert cause in ("pneumonia", "insuficiencia_respiratoria", None)
        if search == "death-respiratory" and not cause:
            raise ValueError("Must specify cause for respiratory")
        elif search == "death-covid" and cause is not None:
            raise ValueError("Cannot specify cause for covid")

        data = {
            "data_type": date_type,
            "search": search,
            "state": state,
            "start_date": str(start_date),
            "end_date": str(end_date),
        }
        if cause is not None:
            data["causa"] = cause
        return scrapy.Request(
            url=urljoin(self.covid_url, "?" + urlencode(data)),
            callback=callback,
            meta={"row": data, "dont_cache": dont_cache},
        )

    # TODO: death-covid &groupBy=gender

    def start_requests(self):
        today = date_utils.today()
        tomorrow = today + datetime.timedelta(days=1)
        # `date_utils.date_range` excludes the last, so to get today's data we
        # need to pass tomorrow.
        for date in date_utils.date_range(datetime.date(2020, 1, 1), tomorrow):
            # Won't cache dates from 7 days ago until today (only historical
            # ones which are unlikely to change).
            should_cache = today - date > datetime.timedelta(days=7)
            for state in STATES:
                for search in ("death-respiratory", "death-covid"):
                    if search == "death-covid":
                        yield self.make_covid_request(
                            start_date=date,
                            end_date=date,
                            date_type="data_ocorrido",
                            search=search,
                            cause=None,
                            state=state,
                            callback=self.parse_covid_request,
                            dont_cache=not should_cache,
                        )
                    else:
                        for cause in ("pneumonia", "insuficiencia_respiratoria"):
                            yield self.make_covid_request(
                                start_date=date,
                                end_date=date,
                                date_type="data_ocorrido",
                                search=search,
                                cause=cause,
                                state=state,
                                callback=self.parse_covid_request,
                                dont_cache=not should_cache,
                            )

    def parse_covid_request(self, response):
        row = response.meta["row"].copy()
        data = json.loads(response.body)

        assert row["start_date"] == row.pop("end_date")
        row["date"] = row.pop("start_date")
        if "causa" not in row:
            row["causa"] = None
        if "dont_cache" in row:
            del row["dont_cache"]

        chart_data = data["chart"]
        if not chart_data:
            row["qtd_2019"] = row["qtd_2020"] = 0
        else:
            if "2019" in chart_data and "2020" in chart_data:
                row["qtd_2019"] = chart_data["2019"]
                row["qtd_2020"] = chart_data["2020"]
            else:
                row["qtd_2019"] = None
                assert len(chart_data.keys()) == 1
                key = list(chart_data.keys())[0]
                day, month = key.split("/")
                assert f"2020-{int(month):02d}-{int(day):02d}" == row["date"]
                row["qtd_2020"] = chart_data[key]
        yield row
