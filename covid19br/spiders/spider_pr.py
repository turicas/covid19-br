import io
from collections import defaultdict

import rows
import scrapy

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.data_normalization_utils import RowsPtBrIntegerField
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    ImportedUndefinedBulletinModel,
)
from covid19br.common.warnings import WarningType


class SpiderPR(BaseCovid19Spider):
    state = State.PR
    name = State.PR.value
    information_delay_in_days = 0
    report_qualities = [
        ReportQuality.COUNTY_BULLETINS,
        ReportQuality.UNDEFINED_OR_IMPORTED_CASES,
    ]

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
                date = self.normalizer.str_to_date(div.xpath(".//p//text()").get())
                url = div.xpath(".//a/@href").get()
                bulletins_per_date[date][filetype] = url

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
        county_reports = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding="utf-8-sig",
            dialect="excel-semicolon",
            force_types={
                "casos": rows.fields.IntegerField,
                "obitos_por_covid_19": rows.fields.IntegerField,
                "obitos": rows.fields.IntegerField,
            },
        )
        for report in county_reports:
            bulletin = CountyBulletinModel(
                date=date,
                state=self.state,
                city=report.municipio,
                confirmed_cases=report.casos,
                deaths=report.obitos_por_covid_19 or report.obitos,
                source=response.request.url,
            )
            self.add_new_bulletin_to_report(bulletin, date)

    def parse_report_pdf(self, response, date):
        """
        Extract imported (outside state) cases and deaths from PDF bulletin
        The information is always on the last page, after 'RESIDENTES FORA DO PARANÁ'.
        """
        last_page = rows.plugins.pdf.number_of_pages(io.BytesIO(response.body))
        full_pdf = rows.plugins.pdf.PyMuPDFBackend(io.BytesIO(response.body))
        table = rows.import_from_pdf(
            io.BytesIO(response.body),
            page_numbers=(last_page,),
            starts_after="RESIDENTES FORA DO PARANÁ",
            force_types={"casos": RowsPtBrIntegerField, "obitos": RowsPtBrIntegerField},
        )
        row = [row for row in table if row.fora_do_pr == "TOTAL"][0]
        source_url = response.request.url
        bulletin = ImportedUndefinedBulletinModel(
            date=date,
            state=self.state,
            confirmed_cases=row.casos,
            deaths=row.obitos,
            source=source_url,
        )
        self.add_new_bulletin_to_report(bulletin, date)
        self._check_pdf_date(full_pdf, date, source_url)

    def _check_pdf_date(self, pdf_content, expected_date, source_url):
        pdf_date = self._extract_pdf_date(pdf_content)
        if pdf_date != expected_date:
            self.add_warning_in_report(
                date=expected_date,
                slug=WarningType.WRONG_DATE_IN_SOURCE,
                description=(
                    f'Era esperado que a data da fonte "{source_url}" de dados importados fosse {expected_date}, '
                    f" porém ela parece ser referente a {pdf_date}. Conferir fonte."
                ),
            )

    def _extract_pdf_date(self, pdf_content):
        first_page_objects = next(pdf_content.text_objects(page_numbers=(1,)))
        for obj in first_page_objects:
            date = self.normalizer.extract_numeric_date(obj.text)
            if date:
                return date
