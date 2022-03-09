import re
import scrapy
from collections import defaultdict

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import StateTotalBulletinModel, CountyBulletinModel

REGEXP_CASES = re.compile("Casos confirmados[  ]+–[  ]+([0-9.]+)")
REGEXP_DEATHS = re.compile("Óbitos[  ]+–[  ]+([0-9.]+)[  ]+[(]")


class SpiderRO(BaseCovid19Spider):
    state = State.RO
    name = State.RO.value
    information_delay_in_days = 0
    report_qualities = [
        ReportQuality.COUNTY_BULLETINS,
    ]

    news_base_url = "https://rondonia.ro.gov.br/"
    news_query_params = "?s=boletim+coronavirus"
    panel_url = "https://covid19.sesau.ro.gov.br/"

    def pre_init(self):
        self.requested_dates = list(self.requested_dates)

    def start_requests(self):
        yield scrapy.Request(self.news_base_url + self.news_query_params)
        yield scrapy.Request(self.panel_url, callback=self.parse_panel)

    def parse(self, response, **kwargs):
        news_per_date = defaultdict(list)
        news_divs = response.xpath("//h2[@class = 'm0']")
        for div in news_divs:
            date = self.normalizer.extract_in_full_date(
                div.xpath(".//small[@class = 'muted']/text()").get()
            )
            url = div.xpath(".//small[@class = 'title']/a[@class = 'bolder']/@href").get()
            news_per_date[date].append(url)

        for date in news_per_date:
            if date in self.requested_dates:
                for link in news_per_date[date]:
                    yield scrapy.Request(
                        link, callback=self.parse_news_bulletin, cb_kwargs={"date": date}
                    )

        # search for other pages if there are missing dates
        if self.start_date < min(news_per_date):
            last_page_number = 1
            last_page_url = response.request.url
            if "pg" in last_page_url:
                *_, page, _query_params = last_page_url.split("/")
                last_page_number = self.normalizer.ensure_integer(page)
            next_page_number = last_page_number + 1
            next_page_url = f"{self.news_base_url}pg/{next_page_number}/{self.news_query_params}"
            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_news_bulletin(self, response, date):
        self._extract_total_from_news(response, date)
        self._extract_cities_from_news(response, date)

    def parse_panel(self, response):
        update_date = self.normalizer.extract_numeric_date(
            response.xpath("//footer//div[contains(@class, 'float-left')]/p[last()]/text()").get()
        )
        if update_date not in self.requested_dates:
            return

        panel_rows = response.xpath("//div[@class = 'row']//div[@class = 'col-md-8']")
        confirmed = None
        deaths = None
        for row in panel_rows:
            if row.xpath("./h6[contains(text(), 'Confirmados')]"):
                confirmed = row.xpath("./h6[contains(@class, 'font-extrabold')]/text()").get()
            elif row.xpath("./h6[contains(text(), 'Óbitos')]"):
                deaths = row.xpath("./h6[contains(@class, 'font-extrabold')]/text()").get()

        bulletin = StateTotalBulletinModel(
            date=update_date,
            state=self.state,
            deaths=deaths,
            confirmed_cases=confirmed,
            source=response.request.url,
        )
        self.add_new_bulletin_to_report(bulletin, update_date)

    def _extract_cities_from_news(self, response, date):
        table = response.xpath("//div[@class = 'entry mt10']//tbody")[0]
        table_rows = table.xpath(".//tr")
        _title, _header, *rows = table_rows
        for row in rows:
            city, confirmed, deaths = row.xpath(".//td//text()").extract()
            if "Total" in city:
                bulletin = StateTotalBulletinModel(
                    date=date,
                    state=self.state,
                    deaths=deaths,
                    confirmed_cases=confirmed,
                    source=response.request.url + " | Total da tabela",
                )
            else:
                bulletin = CountyBulletinModel(
                    date=date,
                    state=self.state,
                    city=city,
                    confirmed_cases=confirmed,
                    deaths=deaths,
                    source=response.request.url,
                )
            self.add_new_bulletin_to_report(bulletin, date)

    def _extract_total_from_news(self, response, date):
        body_text = " ".join(response.xpath("//div[@class = 'entry mt10']//div[not(@class)]//text()").extract())
        cases, *_other_matches = REGEXP_CASES.findall(body_text) or [None]
        deaths, *_other_matches = REGEXP_DEATHS.findall(body_text) or [None]
        if cases or deaths:
            bulletin = StateTotalBulletinModel(
                date=date,
                state=self.state,
                deaths=deaths,
                confirmed_cases=cases,
                source=response.request.url + " | Corpo da notícia",
            )
            self.add_new_bulletin_to_report(bulletin, date)