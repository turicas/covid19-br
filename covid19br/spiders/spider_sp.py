import csv
import io
import logging
import rows
import scrapy

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    ImportedUndefinedBulletinModel,
    StateTotalBulletinModel,
)

logger = logging.getLogger(__name__)

CITY_NAME_CSV_COLUMN = "Município"
CONFIRMED_CASES_CSV_COLUMN = "Mun_Total de casos"
DEATHS_CSV_COLUMN = "Mun_Total de óbitos"
IMPORTED_OR_UNDEFINED_LABELS = ["Outros países", "Outros estados", "Ignorado"]


class SpiderSP(BaseCovid19Spider):
    state = State.SP
    name = State.SP.value
    information_delay_in_days = 0
    report_qualities = [
        ReportQuality.COUNTY_BULLETINS,
        ReportQuality.UNDEFINED_OR_IMPORTED_CASES,
    ]

    total_url = "https://raw.githubusercontent.com/seade-R/dados-covid-sp/master/data/sp.csv"
    source_1_url = "https://raw.githubusercontent.com/seade-R/dados-covid-sp/master/data/dados_covid_sp.csv"
    source2_base_url = "https://www.seade.gov.br"

    def pre_init(self):
        self.requested_dates = list(self.requested_dates)

    def start_requests(self):
        yield scrapy.Request(url=self.total_url, callback=self.parse_csv_total)
        yield scrapy.Request(url=self.source_1_url, callback=self.parse_csv_from_source1)
        if self.today in self.requested_dates:
            yield scrapy.Request(url=f"{self.source2_base_url}/coronavirus/", callback=self.parse_source2)

    def parse_csv_total(self, response):
        total_reports = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding="utf-8-sig",
            dialect="excel-semicolon",
            force_types={
                "datahora": rows.fields.DateField,
                "casos_acum": rows.fields.IntegerField,
                "obitos_acum": rows.fields.IntegerField,
            },
        )
        for report in total_reports:
            if report.datahora in self.requested_dates:
                bulletin = StateTotalBulletinModel(
                    date=report.datahora,
                    state=self.state,
                    confirmed_cases=report.casos_acum,
                    deaths=report.obitos_acum,
                    source=response.request.url,
                )
                self.add_new_bulletin_to_report(bulletin, report.datahora)

    def parse_csv_from_source1(self, response):
        county_reports = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding="utf-8-sig",
            dialect="excel-semicolon",
            force_types={
                "nome_munic": rows.fields.TextField,
                "datahora": rows.fields.DateField,
                "casos": rows.fields.IntegerField,
                "obitos": rows.fields.IntegerField,
                "codigo_ibge": rows.fields.TextField,
                "casos_novos": rows.fields.IntegerField,
                "casos_pc": rows.fields.TextField,
                "casos_mm7d": rows.fields.TextField,
                "obitos_novos": rows.fields.TextField,
                "obitos_pc": rows.fields.TextField,
                "obitos_mm7d": rows.fields.TextField,
                "letalidade": rows.fields.TextField,
                "nome_ra": rows.fields.TextField,
                "cod_ra": rows.fields.TextField,
                "nome_drs": rows.fields.TextField,
                "cod_drs": rows.fields.IntegerField,
                "pop": rows.fields.TextField,
                "semana_epidem": rows.fields.TextField,
            },
        )
        for report in county_reports:
            if report.datahora in self.requested_dates:
                if report.nome_munic == 'Ignorado':
                    bulletin = ImportedUndefinedBulletinModel(
                        date=report.datahora,
                        state=self.state,
                        confirmed_cases=report.casos,
                        deaths=report.obitos,
                        source=response.request.url,
                    )
                else:
                    bulletin = CountyBulletinModel(
                        date=report.datahora,
                        state=self.state,
                        city=report.nome_munic,
                        confirmed_cases=report.casos,
                        deaths=report.obitos,
                        source=response.request.url,
                    )
                self.add_new_bulletin_to_report(bulletin, report.datahora)

    def parse_source2(self, response):
        csv_path = response.xpath(
            "//a[contains(@href, '.csv') and contains(span/text(), 'Municípios')]/@href"
        ).extract_first()
        csv_url = self.source2_base_url + csv_path
        yield scrapy.Request(csv_url, callback=self.parse_csv_from_source2)

    def parse_csv_from_source2(self, response):
        reader = csv.DictReader(
            io.StringIO(response.body.decode("iso-8859-1")), delimiter=";"
        )
        capture_date = self.today
        source = response.request.url

        total_imported_or_undefined_deaths = 0
        total_imported_or_undefined_confirmed_cases = 0
        for row in reader:
            city = row[CITY_NAME_CSV_COLUMN]
            deaths = row[DEATHS_CSV_COLUMN]
            confirmed = row[CONFIRMED_CASES_CSV_COLUMN]

            if city in IMPORTED_OR_UNDEFINED_LABELS:
                total_imported_or_undefined_deaths += self.normalizer.ensure_integer(
                    deaths
                )
                total_imported_or_undefined_confirmed_cases += (
                    self.normalizer.ensure_integer(confirmed)
                )
            elif city:
                bulletin = CountyBulletinModel(
                    date=capture_date,
                    state=self.state,
                    city=city,
                    confirmed_cases=confirmed,
                    deaths=deaths,
                    source=source,
                )
                self.add_new_bulletin_to_report(bulletin, capture_date)
        bulletin = ImportedUndefinedBulletinModel(
            date=capture_date,
            state=self.state,
            confirmed_cases=total_imported_or_undefined_confirmed_cases,
            deaths=total_imported_or_undefined_deaths,
            source=source,
        )
        self.add_new_bulletin_to_report(bulletin, capture_date)
