import datetime
import json
from urllib.parse import urlencode, urljoin

import date_utils
from obitos_spider import BaseRegistroCivilSpider, STATES, qs_to_dict


class TotalDeathsSpider(BaseRegistroCivilSpider):
    name = "obitos_totais"
    base_url = "https://transparencia.registrocivil.org.br/api/record/death"
    start_date = datetime.date(2015, 1, 1)
    end_date = date_utils.today()

    def make_state_request(self, start_date, end_date, state, callback, dont_cache=False):
        data = [
            ("start_date", str(start_date)),
            ("end_date", str(end_date)),
            ("state", state),
        ]
        return self.make_request(
            url=urljoin(self.base_url, "?" + urlencode(data)),
            callback=callback,
            meta={"row": qs_to_dict(data), "dont_cache": dont_cache},
        )

    def start_requests_after_login(self):
        one_day = datetime.timedelta(days=1)
        today = date_utils.today()
        non_cache_period = datetime.timedelta(days=30)
        # `date_utils.date_range` excludes the last, so we need to add one day
        # to `end_date`.
        for date in date_utils.date_range(self.start_date, self.end_date + one_day, interval="monthly"):
            # Won't cache dates from 30 days ago until today (only historical
            # ones which are unlikely to change).
            should_cache = today - date > non_cache_period
            for state in STATES:
                yield self.make_state_request(
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
