import re
import scrapy
from collections import defaultdict

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import StateTotalBulletinModel

REGEXP_CASES = re.compile("([0-9.]+) casos confirmados")
REGEXP_DEATHS = re.compile("([0-9.]+) (?:tiveram [óo]bito confirmado|evolu[ií]ram para [óo]bito)")


class SpiderBA(BaseCovid19Spider):
    state = State.BA
    name = State.BA.value
    information_delay_in_days = 0
    report_qualities = [
        ReportQuality.ONLY_TOTAL,
    ]

    base_url = "http://www.saude.ba.gov.br/category/emergencias-em-saude/"

    def pre_init(self):
        self.requested_dates = list(self.requested_dates)

    def start_requests(self):
        yield scrapy.Request(
            self.base_url,
            meta={'download_timeout': 3}
        )

    def parse(self, response, **kwargs):
        news_per_date = defaultdict(list)
        news_divs = response.xpath("//div[@class = 'noticia']")
        for div in news_divs:
            titulo = div.xpath(".//h2//text()").get()
            if self.is_covid_report_news(titulo):
                datahora = self.normalizer.str_to_datetime(
                    div.xpath(".//p[@class = 'data-hora']/text()").get()
                )
                url = div.xpath(".//h2/a/@href").get()
                news_per_date[datahora.date()].append(url)

        for date in news_per_date:
            if date in self.requested_dates:
                for link in news_per_date[date]:
                    yield scrapy.Request(
                        link, callback=self.parse_bulletin_text, cb_kwargs={"date": date}
                    )

        if self.start_date < min(news_per_date):
            last_page_number = 1
            last_page_url = response.request.url
            if "page" in last_page_url:
                url, *_query_params = last_page_url.split("?")
                if url[-1] == "/":
                    url = url[:-1]
                *_url_path, last_page_number = url.split("/")
                last_page_number = self.normalizer.ensure_integer(last_page_number)
            next_page_number = last_page_number + 1
            next_page_url = f"{self.base_url}page/{next_page_number}/"
            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_bulletin_text(self, response, date):
        html = response.text
        cases, *_other_matches = REGEXP_CASES.findall(html) or [None]
        deaths, *_other_matches = REGEXP_DEATHS.findall(html) or [None]
        if cases or deaths:
            bulletin = StateTotalBulletinModel(
                date=date,
                state=self.state,
                deaths=deaths,
                confirmed_cases=cases,
                source=response.request.url,
            )
            self.add_new_bulletin_to_report(bulletin, date)

    @staticmethod
    def is_covid_report_news(news_title: str) -> bool:
        clean_title = news_title.lower()
        return "bahia" in clean_title and "covid" in clean_title
