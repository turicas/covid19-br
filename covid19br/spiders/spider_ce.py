import json
from collections import defaultdict
from typing import List

import scrapy

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State, ReportQuality
from covid19br.common.models.bulletin_models import (
    CountyBulletinModel,
    ImportedUndefinedBulletinModel,
)

CONFIRMED_CASE_LABEL = "Confirmados"
DEATH_CASE_LABEL = "Óbitos"
IMPORTED_OR_UNDEFINED_LABEL = "SEM INFORMAÇÃO"


class SpiderCE(BaseCovid19Spider):
    state = State.CE
    name = State.CE.value
    information_delay_in_days = 0
    report_qualities = [
        ReportQuality.COUNTY_BULLETINS,
        ReportQuality.UNDEFINED_OR_IMPORTED_CASES,
    ]

    base_url = "https://indicadores.integrasus.saude.ce.gov.br/api/coronavirus/qtd-por-municipio"

    def start_requests(self):
        for date in self.dates_range:
            if date == self.today:
                link = f"{self.base_url}"
            else:
                date_str = date.strftime("%Y-%m-%d")
                link = f"{self.base_url}?dataFim={date_str}"
            yield scrapy.Request(link, callback=self.parse, cb_kwargs={"date": date})

    def parse(self, response, **kwargs):
        date = kwargs["date"]
        data = json.loads(response.body)
        source = response.request.url

        cases_by_city = self.group_cases_by_city(data)
        for city, cases in cases_by_city.items():
            if city == IMPORTED_OR_UNDEFINED_LABEL:
                bulletin = ImportedUndefinedBulletinModel(
                    date=date,
                    state=self.state,
                    confirmed_cases=cases.get(CONFIRMED_CASE_LABEL),
                    deaths=cases.get(DEATH_CASE_LABEL),
                    source_url=source,
                )
            else:
                bulletin = CountyBulletinModel(
                    date=date,
                    state=self.state,
                    city=city,
                    confirmed_cases=cases.get(CONFIRMED_CASE_LABEL),
                    deaths=cases.get(DEATH_CASE_LABEL),
                    source_url=source,
                )
            self.add_new_bulletin_to_report(bulletin, date)

    @staticmethod
    def group_cases_by_city(data: List[dict]) -> dict:
        cases_by_city = defaultdict(dict)
        for report in data:
            report_type = report.get("tipo")
            city = report.get("municipio")
            cases = report.get("quantidade")
            if report_type == CONFIRMED_CASE_LABEL or report_type == DEATH_CASE_LABEL:
                cases_by_city[city][report_type] = cases
        return cases_by_city
