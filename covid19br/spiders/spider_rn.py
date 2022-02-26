import scrapy
import tempfile

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    StateTotalBulletinModel,
)
from covid19br.parsers.rio_grande_do_norte import RioGrandeDoNorteBulletinExtractor


class SpiderRN(BaseCovid19Spider):
    state = State.RN
    name = State.RN.value
    information_delay_in_days = 1
    report_qualities = [ReportQuality.COUNTY_BULLETINS]

    start_urls = [
        "http://www.saude.rn.gov.br/Conteudo.asp?TRAN=ITEM&TARG=240728&ACT=&PAGE=0&PARM=&LBL=ACERVO+DE+MAT%C9RIAS"
    ]

    def parse(self, response, **kwargs):
        bulletins_per_date = {}
        bulletins = response.xpath(
            "(//li[strong[a[contains(@href, 'PDF')]]]) | (//li[a[contains(@href, 'PDF')]])"
        )
        for bulletin in bulletins:
            pdf_url = bulletin.xpath(".//@href").get()
            raw_description = " ".join(bulletin.xpath(".//text()").extract())
            bulletin_date = self.normalizer.extract_numeric_date(raw_description)
            if bulletin_date:
                bulletins_per_date[bulletin_date] = pdf_url

        for date in self.requested_dates:
            url = bulletins_per_date.get(date)
            if url:
                yield scrapy.Request(url, callback=self.parse_pdf)

    def parse_pdf(self, response):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf") as tmp:
            tmp.write(response.body)

            extractor = RioGrandeDoNorteBulletinExtractor(tmp.name)
            date = extractor.date

            deaths, confirmed = extractor.official_totals
            bulletin = StateTotalBulletinModel(
                date=date,
                state=self.state,
                confirmed_cases=confirmed,
                deaths=deaths,
                source=response.request.url + " | Painel na primeira página do pdf.",
            )
            self.add_new_bulletin_to_report(bulletin, date)

            for row in extractor.data:
                city, confirmed, deaths = row
                if city == "rn":
                    bulletin = StateTotalBulletinModel(
                        date=date,
                        state=self.state,
                        confirmed_cases=confirmed,
                        deaths=deaths,
                        source=response.request.url + " | Total na tabela do pdf.",
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
