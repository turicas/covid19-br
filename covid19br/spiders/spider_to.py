import datetime
import json
import scrapy
import tempfile

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    StateTotalBulletinModel,
)
from covid19br.parsers.tocantins import TocantinsBulletinExtractor


EXPRESSION_FOR_DEATH_PLUS_CONFIRMED_CASES = (
    "Distribuição dos casos e óbitos confirmados acumulados"
)


class SpiderTO(BaseCovid19Spider):
    state = State.TO
    name = State.TO.value
    information_delay_in_days = 1
    report_qualities = [ReportQuality.COUNTY_BULLETINS]

    start_urls = ["https://www.to.gov.br/saude/boletim-covid-19/3vvgvo8csrl6"]

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
            bulletins_per_date[self._extract_date(raw_date_text)] = pdf_url

        for date in self.requested_dates:
            url = bulletins_per_date.get(date)
            if url:
                yield scrapy.Request(url, callback=self.parse_pdf)

        # getting via API the official total displayed on http://integra.saude.to.gov.br/covid19
        yield scrapy.Request(
            "http://integra.saude.to.gov.br/Api/GetAtualizacaoCoronaTO?idPainel=31",
            callback=self.get_official_total,
        )

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
                        source=response.request.url,
                    )
                else:
                    bulletin = CountyBulletinModel(
                        date=date,
                        state=self.state,
                        city=row["city"],
                        confirmed_cases=row["confirmed"],
                        deaths=row["deaths"],
                        source=response.request.url,
                    )
                self.add_new_bulletin_to_report(bulletin, date)

    def _extract_date(self, value) -> datetime.date:
        """
        >>> extract_date("10 de fevereiro de 2022.pdf")
        datetime.date(2022, 2, 10)
        >>> extract_date("07 janeiro de 2022.pdf")
        datetime.date(2022, 1, 7)
        >>> extract_date("BOLETIM COVID 30-11-21.pdf")
        datetime.date(2021, 11, 30)
        >>> extract_date("BOLETIM COVID 29-11-21 (1).pdf")
        datetime.date(2021, 11, 29)
        >>> extract_date("25 de Novembro")
        datetime.date(2020, 11, 25)
        >>> extract_date("file_open 24 de julho de 2021")
        datetime.date(2021, 07, 24)
        """
        if "BOLETIM" in value:
            return self.normalizer.extract_numeric_date(value)
        return self.normalizer.extract_in_full_date(value)

    def get_official_total(self, response):
        resp = json.loads(response.body)
        result = json.loads(resp.get("Resultado", "{}"))
        published_at = result.get("resultset", [[None]])[0][0]
        source = "http://integra.saude.to.gov.br/covid19 | " + resp.get("Rodape", "")

        published_at_date = self.normalizer.extract_in_full_date(published_at)
        if published_at_date in self.requested_dates:
            official_total = StateTotalBulletinModel(
                date=published_at_date, state=self.state, source=source
            )
            yield scrapy.Request(
                "http://integra.saude.to.gov.br/Api/GetReleasesCovid?id=247",
                callback=self.get_official_confirmed_cases,
                cb_kwargs={"date": published_at_date, "official_total": official_total},
            )

    def get_official_confirmed_cases(self, response, date, official_total):
        resp = json.loads(response.body)
        if "casos confirmados" in resp.get("NomePainel", "").lower():
            cases = json.loads(resp.get("Retorno", "{}")).get("resultset", [[0]])[0][0]
            official_total.increase_confirmed_cases(cases)
            yield scrapy.Request(
                "http://integra.saude.to.gov.br/Api/GetReleasesCovid?id=249",
                callback=self.get_official_deaths,
                cb_kwargs={"date": date, "official_total": official_total},
            )

    def get_official_deaths(self, response, date, official_total):
        resp = json.loads(response.body)
        panel_name = self.normalizer.remove_accentuation(
            resp.get("NomePainel", "").lower()
        )
        if "obitos" in panel_name:
            cases = json.loads(resp.get("Retorno", "{}")).get("resultset", [[0]])[0][0]
            official_total.increase_deaths(cases)
            self.add_new_bulletin_to_report(official_total, date)
