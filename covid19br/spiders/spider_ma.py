import re

import scrapy
from collections import defaultdict
from datetime import datetime

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality


class SpiderMA(BaseCovid19Spider):
    state = State.MA
    name = State.MA.value
    information_delay_in_days = 0
    report_qualities = [
        ReportQuality.COUNTY_BULLETINS,
    ]

    base_url = "https://www.saude.ma.gov.br/boletins-covid-19"

    def pre_init(self):
        self.requested_dates = list(self.requested_dates)

    def start_requests(self):
        current_year = self.today.year
        requested_years = set([date.year for date in self.requested_dates])
        for year in requested_years:
            if year == current_year:
                yield scrapy.Request(self.base_url + "/")
            else:
                yield scrapy.Request(f"{self.base_url}-{year}/")

    def parse(self, response, **kwargs):
        bulletins_per_date = defaultdict(dict)
        divs = response.xpath("//div[@class='wpb_wrapper']//a")
        for div in divs:
            div_text = self.normalizer.remove_accentuation((div.xpath("./text()").get() or "").lower())
            div_url = div.xpath("./@href").get()
            if 'dados gerais em csv' in div_text:
                date = self._extract_date_from_csv_name(div_url)
                bulletins_per_date[date]["csv"] = div_url
            elif 'boletim epidemiologico' in div_text:
                date = self.normalizer.extract_in_full_date(div_text)
                bulletins_per_date[date]["pdf"] = div_url

        for date in self.requested_dates:
            if date in bulletins_per_date:
                urls = bulletins_per_date[date]
                csv_url = urls.get("csv")
                pdf_url = urls.get("pdf")
                if csv_url:
                    yield scrapy.Request(
                        csv_url,
                        callback=self.parse_reports_csv,
                        cb_kwargs={"date": date},
                    )
                if pdf_url:
                    yield scrapy.Request(
                        pdf_url,
                        callback=self.parse_report_pdf,
                        cb_kwargs={"date": date},
                    )

    def parse_reports_csv(self, response, date):
        print(response.request.url)
        pass

    def parse_report_pdf(self, response, date):
        print(response.request.url)
        pass

    @staticmethod
    def _extract_date_from_csv_name(csv_name) -> datetime.date:
        year = csv_name.split("uploads/")[-1].split("/")[0]
        date_month, *_ = re.compile("[0-9]+").findall(csv_name.split("/")[-1]) or [None]
        if date_month:
            if len(date_month) <= 4:
                month, day = date_month[-2:], date_month[-4:-2]
            else:
                month, day = date_month[2:4], date_month[0:2]
            return datetime(int(year), int(month), int(day)).date()

