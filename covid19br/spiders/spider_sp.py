import csv
import io
import logging

import scrapy

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    ImportedUndefinedBulletinModel,
)

logger = logging.getLogger(__name__)

CITY_NAME_CSV_COLUMN = "Município"
CONFIRMED_CASES_CSV_COLUMN = "Mun_Total de casos"
DEATHS_CSV_COLUMN = "Mun_Total de óbitos"
IMPORTED_OR_UNDEFINED_LABELS = ["Outros países", "Outros estados", "Ignorado"]


class SpiderSP(BaseCovid19Spider):
    state = State.SP
    name = State.SP.value

    base_url = "https://www.seade.gov.br"
    start_urls = [f"{base_url}/coronavirus/"]

    def pre_init(self):
        logger.warning(
            "This spider only gathers data for the current date. "
            "It does not consider any given 'dates_range'."
        )

    def parse(self, response, **kwargs):
        csv_path = response.xpath(
            "//a[contains(@href, '.csv') and contains(span/text(), 'Municípios')]/@href"
        ).extract_first()
        csv_url = self.base_url + csv_path
        yield scrapy.Request(csv_url, callback=self.parse_csv)

    def parse_csv(self, response, **kwargs):
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
                    source_url=source,
                )
                self.add_new_bulletin_to_report(bulletin, capture_date)
        bulletin = ImportedUndefinedBulletinModel(
            date=capture_date,
            state=self.state,
            confirmed_cases=total_imported_or_undefined_confirmed_cases,
            deaths=total_imported_or_undefined_deaths,
            source_url=source,
        )
        self.add_new_bulletin_to_report(bulletin, capture_date)
