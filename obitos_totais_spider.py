import datetime
import json
from urllib.parse import urlencode, urljoin

import scrapy

import date_utils
from obitos_spider import STATES, qs_to_dict


class DeathsSpider(scrapy.Spider):
    name = "obitos_totais"
    base_url = "https://transparencia.registrocivil.org.br/api/record/death"


    def make_request(
        self, start_date, end_date, state, callback, dont_cache=False
    ):
        data = [
            ("start_date", str(start_date)),
            ("end_date", str(end_date)),
            ("state", state),
        ]
        return scrapy.Request(
            url=urljoin(self.base_url, "?" + urlencode(data)),
            callback=callback,
            meta={"row": qs_to_dict(data), "dont_cache": dont_cache},
        )

    def start_requests(self):
        # TODO: criar BaseRegistroCivilSpider com start_requests e herdar dela
        one_day = datetime.timedelta(days=1)
        today = date_utils.today()
        tomorrow = today + datetime.timedelta(days=1)
        # `date_utils.date_range` excludes the last, so to get today's data we
        # need to pass tomorrow.
        for date in date_utils.date_range(datetime.date(2015, 1, 1), tomorrow, interval="monthly"):
            # Won't cache dates from 30 days ago until today (only historical
            # ones which are unlikely to change).
            should_cache = today - date > datetime.timedelta(days=30)
            for state in STATES:
                yield self.make_request(
                    start_date=date,
                    end_date=date_utils.next_date(date, "monthly") - one_day,
                    state=state,
                    callback=self.parse,
                    dont_cache=not should_cache,
                )

    def parse(self, response):
        meta = response.meta["row"]
        data = json.loads(response.body)["data"]
        for row in data:
            row.update(meta)
            row["city"] = row.pop("name")
            row["deaths_total"] = row.pop("total")
            yield row
