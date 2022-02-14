import io
import re
import datetime
import tempfile

import rows
import scrapy

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State
from covid19br.common.models.bulletin_models import CountyBulletinModel, StateTotalBulletinModel
from covid19br.parsers.tocantins import MONTHS, TocantinsBulletinExtractor


EXPRESSION_FOR_DEATH_PLUS_CONFIRMED_CASES = (
    "Distribuição dos casos e óbitos confirmados acumulados"
)
REGEXP_DATE = re.compile("([0-9]{1,2})(?: +de)? ([^ ]+)(?: de ([0-9]{4}))?")
REGEXP_DATE_2 = re.compile("([0-9]{2})-([0-9]{2})-([0-9]{2,4})[ .]?")

def extract_date(value):
    """
    >>> extract_date("10 de fevereiro de 2022.pdf")
    datetime.date(2022, 2, 10)
    >>> extract_date("07 janeiro de 2022.pdf")
    datetime.date(2022, 1, 7)
    >>> extract_date("BOLETIM COVID 30-11-21.pdf")
    datetime.date(2021, 11, 30)
    >>> extract_date("25 de Novembro")
    datetime.date(2020, 11, 25)
    """

    if "BOLETIM" in value:
        result = REGEXP_DATE_2.findall(value)
    else:
        result = REGEXP_DATE.findall(value)
    day, month, year = result[0]
    year = int(year) if year else 2020
    year = year if year > 2000 else 2000 + year
    month = int(month) if month.isdigit() else MONTHS.index(month.lower()[:3]) + 1
    return datetime.date(year, month, int(day))


class SpiderTO(BaseCovid19Spider):
    state = State.TO
    name = State.TO.value

    start_urls = ["https://www.to.gov.br/saude/boletim-covid-19/3vvgvo8csrl6"]

    has_official_total = False

    def parse(self, response, **kwargs):
        bulletins_per_date = {}
        bulletins = response.xpath(
            '//div[contains(@class, "page_extra_files")]//ul//a[contains(@href, "/download/")]'
        )
        for bulletin in bulletins:
            pdf_url = bulletin.xpath(".//@href").get()
            raw_date_text = bulletin.xpath(".//span//text()").get() or "".join(
                bulletin.xpath(".//text()").extract()
            )
            bulletins_per_date[extract_date(raw_date_text)] = pdf_url

        for date in self.dates_range:
            url = bulletins_per_date.get(date)
            if url:
                yield scrapy.Request(url, callback=self.parse_pdf)

    def parse_pdf(self, response):
        """Converte PDF do boletim COVID-19 do Tocantins em CSV"""

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf") as tmp:
            tmp.write(response.body)

            extractor = TocantinsBulletinExtractor(tmp.name)
            date = extractor.date
            for row in extractor.data:
                if row["city"].lower() in ("total", "", None):
                    bulletin = StateTotalBulletinModel(
                        date=date,
                        state=self.state,
                        confirmed_cases=row["confirmed"],
                        deaths=row["deaths"],
                        source_url=response.request.url,
                    )
                    self.has_official_total = True
                else:
                    bulletin = CountyBulletinModel(
                        date=date,
                        state=self.state,
                        city=row["city"],
                        confirmed_cases=row["confirmed"],
                        deaths=row["deaths"],
                        source_url=response.request.url,
                    )
                self.add_new_bulletin_to_report(bulletin, date, auto_increase_cases=(not self.has_official_total))
