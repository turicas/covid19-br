import io
from collections import defaultdict

import rows
import scrapy

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State
from covid19br.common.data_normalization_utils import RowsPtBrIntegerField
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    ImportedUndefinedBulletinModel,
)


class SpiderPR(BaseCovid19Spider):
    state = State.PR
    name = State.PR.value

    start_urls = ["https://www.saude.pr.gov.br/Pagina/Coronavirus-COVID-19"]

    def parse(self, response, **kwargs):
        bulletins_per_date = defaultdict(dict)
        filetype_divs = {
            "csv": response.xpath(
                "//div[contains(@class, 'row row-') and contains(.//a//text(), 'Casos e Óbitos') and contains(.//a/@href, '.csv')]"
            ),
            "pdf": response.xpath(
                "//div[contains(@class, 'row row-') and contains(.//a//text(), 'Informe Completo') and contains(.//a/@href, '.pdf')]"
            ),
        }
        for filetype, divs in filetype_divs.items():
            for div in divs:
                date = self.normalizer.extract_date(div.xpath(".//p//text()").get())
                url = div.xpath(".//a/@href").get()
                bulletins_per_date[date][filetype] = url

        for date in self.dates_range:
            if date in bulletins_per_date:
                urls = bulletins_per_date[date]
                yield scrapy.Request(
                    urls["csv"],
                    callback=self.parse_reports_csv,
                    cb_kwargs={"date": date},
                )
                yield scrapy.Request(
                    urls["pdf"],
                    callback=self.parse_report_pdf,
                    cb_kwargs={"date": date},
                )

    def parse_reports_csv(self, response, date):
        county_reports = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding="utf-8-sig",
            dialect="excel-semicolon",
            force_types={
                "casos": rows.fields.IntegerField,
                "obitos": rows.fields.IntegerField,
            },
        )
        for report in county_reports:
            bulletin = CountyBulletinModel(
                date=date,
                state=self.state,
                city=report.municipio,
                confirmed_cases=report.casos,
                deaths=report.obitos,
                source_url=response.request.url,
            )
            self.add_new_bulletin_to_report(bulletin, date)

    def parse_report_pdf(self, response, date):
        """
        Extract imported (outside state) cases and deaths from PDF bulletin
        The information is always on the last page, after 'RESIDENTES FORA DO PARANÁ'.
        """
        last_page = rows.plugins.pdf.number_of_pages(io.BytesIO(response.body))
        table = rows.import_from_pdf(
            io.BytesIO(response.body),
            page_numbers=(last_page,),
            starts_after="RESIDENTES FORA DO PARANÁ",
            force_types={"casos": RowsPtBrIntegerField, "obitos": RowsPtBrIntegerField},
        )
        for row in table:
            if row.fora_do_pr == "TOTAL":
                bulletin = ImportedUndefinedBulletinModel(
                    date=date,
                    state=self.state,
                    confirmed_cases=row.casos,
                    deaths=row.obitos,
                    source_url=response.request.url,
                )
                self.add_new_bulletin_to_report(bulletin, date)
                return
