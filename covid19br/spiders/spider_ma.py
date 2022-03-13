import io
import re
import rows
import scrapy
from collections import defaultdict
from datetime import datetime

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    StateTotalBulletinModel,
)

CITY_NAME_CSV_COLUMN = 0
CONFIRMED_CASES_CSV_COLUMN = 1
DEATH_CASES_CSV_COLUMN = 2


class SpiderMA(BaseCovid19Spider):
    state = State.MA
    name = State.MA.value
    information_delay_in_days = 0
    report_qualities = [ReportQuality.COUNTY_BULLETINS]

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
            div_text = self.normalizer.remove_accentuation(
                (div.xpath("./text()").get() or "").lower()
            )
            div_url = div.xpath("./@href").get()
            if "dados gerais em csv" in div_text:
                date = self._extract_date_from_csv_name(div_url)
                bulletins_per_date[date]["csv"] = div_url
            elif "boletim epidemiologic" in div_text:
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
        # TODO: handle files that need to be opened in universal-newline mode (ex: csv from 2022-03-06)
        data = rows.import_from_csv(
            io.BytesIO(response.body), encoding="latin-1", dialect="excel-semicolon"
        )
        # remove empty lines at the end of the file
        data = [row for row in data if row[CITY_NAME_CSV_COLUMN]]

        _headers, county_reports = data[:2], data[2:]
        for report in county_reports:
            name = report[CITY_NAME_CSV_COLUMN].lower()
            deaths = report[DEATH_CASES_CSV_COLUMN]
            cases = report[CONFIRMED_CASES_CSV_COLUMN]

            if "revisão" in name:
                self.add_note_in_report(date, f"- Nota no csv: {name}")
            elif "total" in name:
                bulletin = StateTotalBulletinModel(
                    date=date,
                    state=self.state,
                    deaths=deaths,
                    confirmed_cases=cases,
                    source=response.request.url,
                )
                self.add_new_bulletin_to_report(bulletin, date)
            else:
                bulletin = CountyBulletinModel(
                    date=date,
                    state=self.state,
                    city=name,
                    confirmed_cases=cases,
                    deaths=deaths,
                    source=response.request.url,
                )
                self.add_new_bulletin_to_report(bulletin, date)

    def parse_report_pdf(self, response, date):
        source = response.request.url
        doc = rows.plugins.pdf.PyMuPDFBackend(io.BytesIO(response.body))
        first_page_objs = next(doc.text_objects())

        pdf_date = self._get_pdf_date(first_page_objs)
        if pdf_date and pdf_date != date:
            self.logger.warning(
                f"PDF date does not match for pdf {source}. Aborting extraction."
            )
            return

        confirmed_cases_label = next(
            obj for obj in first_page_objs if obj.text.lower() == "confirmados"
        )
        deaths_label = next(
            obj for obj in first_page_objs if obj.text.lower() == "óbitos"
        )

        # select the number above and on the left of confirmed_cases_label
        confirmed_cases = next(
            obj
            for obj in first_page_objs
            if self._is_only_number(obj.text)
            and obj.y0 < confirmed_cases_label.y0
            and obj.x0 < confirmed_cases_label.x0
        )
        # select the numbers above and that are in the same column as deaths_label and pick the closest one
        deaths, *_ = sorted(
            [
                obj
                for obj in first_page_objs
                if self._is_only_number(obj.text)
                and obj.y0 < deaths_label.y0
                and obj.x0 < deaths_label.x0
                and obj.x1 > deaths_label.x1
            ],
            key=lambda obj: deaths_label.y0 - obj.y0,
        ) or [None]

        bulletin = StateTotalBulletinModel(
            date=date,
            state=self.state,
            deaths=deaths.text,
            confirmed_cases=confirmed_cases.text,
            source=response.request.url,
        )
        self.add_new_bulletin_to_report(bulletin, date)

    def _get_pdf_date(self, text_objs):
        for obj in text_objs:
            if "BOLETIM ATUALIZADO" in obj.text:
                return self.normalizer.extract_numeric_date(obj.text)

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

    @staticmethod
    def _is_only_number(value):
        return re.compile("^([0-9.]+)$").findall(value.strip())
