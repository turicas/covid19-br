import re
import scrapy

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import StateTotalBulletinModel


REGEXP_CASES = re.compile("o Acre registra ([0-9.]+)(?:.+) de contaminação pela doença")
REGEXP_DEATHS = re.compile(
    "o número oficial de mortes por covid-19 (?:.+) ([0-9.]+)[,]? em todo o estado"
)


class SpiderAC(BaseCovid19Spider):
    state = State.AC
    name = State.AC.value
    information_delay_in_days = 0
    report_qualities = [ReportQuality.COUNTY_BULLETINS]

    news_base_url = "https://agencia.ac.gov.br/"
    news_query_params = "?s=covid19"

    def pre_init(self):
        self.requested_dates = list(self.requested_dates)

    def start_requests(self):
        yield scrapy.Request(self.news_base_url + self.news_query_params)

    def parse(self, response, **kwargs):
        news_per_date = {}
        news_divs = response.xpath("//header[@class='entry-header']")
        for div in news_divs:
            url = div.xpath(".//h2[@class='entry-title']//a/@href").get()
            if "boletim-sesacre" in url:
                raw_date = (
                    div.xpath(".//span[@class='date-post']//text()[2]").get().strip()
                )
                date = self.normalizer.extract_numeric_date(raw_date)
                news_per_date[date] = url

        for date in news_per_date:
            if date in self.requested_dates:
                yield scrapy.Request(
                    news_per_date[date],
                    callback=self.parse_news_bulletin,
                    cb_kwargs={"date": date},
                )

        # handle pagination
        if news_per_date and self.start_date < min(news_per_date):
            last_page_number = 1
            last_page_url = response.request.url
            if "page" in last_page_url:
                url, *_query_params = last_page_url.split("?")
                if url[-1] == "/":
                    url = url[:-1]
                *_url_path, last_page_number = url.split("/")
                last_page_number = self.normalizer.ensure_integer(last_page_number)
            next_page_number = last_page_number + 1
            next_page_url = (
                f"{self.news_base_url}page/{next_page_number}/{self.news_query_params}"
            )
            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_news_bulletin(self, response, date):
        self._extract_cases_and_deaths_from_news(response, date)

        pdf_url = response.xpath(
            "//div[@class='entry-content']//a[contains(@href, '.pdf') and contains(@href, 'BOLETIM')]/@href"
        ).get()
        yield scrapy.Request(
            pdf_url, callback=self.parse_pdf_bulletin, cb_kwargs={"date": date}
        )

    def parse_pdf_bulletin(self, response, date):
        print(f"Let's que let's {response.request.url}")

    def _extract_cases_and_deaths_from_news(self, response, date):
        body_text = " ".join(
            response.xpath("//div[@class='entry-content']//p//text()").extract()
        )
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
