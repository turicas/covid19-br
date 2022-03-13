import logging
from collections import defaultdict
import re
import scrapy
import tempfile

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import (
    StateTotalBulletinModel,
    CountyBulletinModel,
)
from covid19br.parsers.rondonia import RondoniaBulletinExtractor

REGEXP_CASES = re.compile("Casos confirmados[  ]+–[  ]+([0-9.]+)")
REGEXP_DEATHS = re.compile("Óbitos[  ]+–[  ]+([0-9.]+)[  ]+[(]")


class SpiderRO(BaseCovid19Spider):
    state = State.RO
    name = State.RO.value
    information_delay_in_days = 0
    report_qualities = [ReportQuality.COUNTY_BULLETINS]

    news_base_url = "https://rondonia.ro.gov.br/"
    news_query_params = "?s=boletim+coronavirus"
    panel_url = "https://covid19.sesau.ro.gov.br/"
    pdf_reports_url = (
        "https://rondonia.ro.gov.br/covid-19/noticias/relatorios-de-acoes-sci/"
    )

    def pre_init(self):
        self.requested_dates = list(self.requested_dates)

    def start_requests(self):
        yield scrapy.Request(self.news_base_url + self.news_query_params)
        yield scrapy.Request(self.pdf_reports_url, callback=self.parse_pdfs_page)
        yield scrapy.Request(self.panel_url, callback=self.parse_panel)

    def parse(self, response, **kwargs):
        news_per_date = defaultdict(list)
        news_divs = response.xpath("//h2[@class = 'm0']")
        for div in news_divs:
            date = self.normalizer.extract_in_full_date(
                div.xpath(".//small[@class = 'muted']/text()").get()
            )
            url = div.xpath(".//small[@class='title']/a[@class='bolder']/@href").get()
            news_per_date[date].append(url)

        for date in news_per_date:
            if date in self.requested_dates:
                for link in news_per_date[date]:
                    yield scrapy.Request(
                        link,
                        callback=self.parse_news_bulletin,
                        cb_kwargs={"date": date},
                    )

        # search for other pages if there are missing dates
        if self.start_date < min(news_per_date):
            last_page_number = 1
            last_page_url = response.request.url
            if "pg" in last_page_url:
                *_, page, _query_params = last_page_url.split("/")
                last_page_number = self.normalizer.ensure_integer(page)
            next_page_number = last_page_number + 1
            next_page_url = (
                f"{self.news_base_url}pg/{next_page_number}/{self.news_query_params}"
            )
            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_news_bulletin(self, response, date):
        self._extract_total_from_news(response, date)
        self._extract_cities_from_news(response, date)

    def parse_panel(self, response):
        update_date = self.normalizer.extract_numeric_date(
            response.xpath(
                "//footer//div[contains(@class, 'float-left')]/p[last()]/text()"
            ).get()
        )
        if update_date not in self.requested_dates:
            return

        panel_rows = response.xpath("//div[@class = 'row']//div[@class = 'col-md-8']")
        confirmed = None
        deaths = None
        for row in panel_rows:
            if row.xpath("./h6[contains(text(), 'Confirmados')]"):
                confirmed = row.xpath(
                    "./h6[contains(@class, 'font-extrabold')]/text()"
                ).get()
            elif row.xpath("./h6[contains(text(), 'Óbitos')]"):
                deaths = row.xpath(
                    "./h6[contains(@class, 'font-extrabold')]/text()"
                ).get()

        bulletin = StateTotalBulletinModel(
            date=update_date,
            state=self.state,
            deaths=deaths,
            confirmed_cases=confirmed,
            source=response.request.url,
        )
        self.add_new_bulletin_to_report(bulletin, update_date)

    def parse_pdfs_page(self, response):
        divs = response.xpath(
            "//a[contains(@href, '.pdf') and contains(text(), 'Sala')]"
        )
        pdf_per_date = {}
        for div in divs:
            pdf_url = div.xpath("./@href").get()
            pdf_date = self._extract_date_from_pdf_url(pdf_url)
            bulletin_name = (
                div.xpath(".//text()").extract_first().replace("\xa0", " ").upper()
            )
            if pdf_date in pdf_per_date and not "RETIFICADO" in bulletin_name:
                continue
            pdf_per_date[pdf_date] = pdf_url

        for date in pdf_per_date:
            if date in self.requested_dates:
                yield scrapy.Request(
                    pdf_per_date[date],
                    callback=self.parse_pdf_report,
                    cb_kwargs={"date": date},
                )

    def parse_pdf_report(self, response, date):
        with tempfile.NamedTemporaryFile(mode="wb") as tmp:
            tmp.write(response.body)
            try:
                extractor = RondoniaBulletinExtractor(tmp.name)
            except RuntimeError:  # The file is not a PDF (probably HTML)
                logging.log(
                    logging.ERROR,
                    f"File is not PDF for bulletin: {response.request.url}",
                )
                return
            try:
                bulletin_data = extractor.data
            except RuntimeError:
                logging.log(
                    logging.ERROR,
                    "This parser does not work for bulletins before 2021-01-18",
                )
                return

            bulletin_date = extractor.date or date
            for row in bulletin_data:
                if row["municipio"] == "TOTAL NO ESTADO":
                    bulletin = StateTotalBulletinModel(
                        date=date,
                        state=self.state,
                        confirmed_cases=row["confirmados"],
                        deaths=row["mortes"],
                        source=response.request.url,
                    )
                else:
                    bulletin = CountyBulletinModel(
                        date=date,
                        state=self.state,
                        city=row["municipio"],
                        confirmed_cases=row["confirmados"],
                        deaths=row["mortes"],
                        source=response.request.url,
                    )
                self.add_new_bulletin_to_report(bulletin, bulletin_date)

    def _extract_cities_from_news(self, response, date):
        table = response.xpath("//div[@class='entry mt10']//tbody")[0]
        table_rows = table.xpath(".//tr")
        _title, _header, *rows = table_rows
        for row in rows:
            city, confirmed, deaths, *extra = row.xpath(".//td//text()").extract()
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
        body_text = " ".join(
            response.xpath(
                "//div[@class = 'entry mt10']//div[not(@class)]//text()"
            ).extract()
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

    def _extract_date_from_pdf_url(self, pdf_url: str):
        *rest, relevant_content = pdf_url.split("uploads/")
        if not rest:
            *rest, relevant_content = pdf_url.split("data.portal.sistemas.ro.gov.br/")

        year, *_, text_with_date = relevant_content.split("/")
        year = self.normalizer.ensure_integer(year)
        text_with_date = re.sub(r"[.-]", r" ", text_with_date)

        # fix cases like "0 8 de Março de 2022"
        text_with_date = re.sub(r"(\d) (\d)", r"$1$2", text_with_date)
        # fix cases like "28de Agosto de 2021"
        text_with_date = re.sub(r"(\d+)(de)", r"\1 \2", text_with_date)

        try:
            return self.normalizer.extract_in_full_date(
                text_with_date, default_year=year
            )
        except ValueError:
            # TODO: implement a mechanism to infer the date based on the report number edition
            pass
