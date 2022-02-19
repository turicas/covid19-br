import datetime
import logging
from abc import ABC
from typing import Dict, List

import scrapy
from rows.utils.date import date_range

from covid19br.common.constants import State, ReportQuality
from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.common.models.full_report import BulletinModel, FullReportModel

logger = logging.getLogger(__name__)


class BaseCovid19Spider(scrapy.Spider, ABC):
    """
    Responsible for defining the interface with the crawler engine (scrapy)
    and the brasil.io backend.
    Knows how to gather the covid19 data for a state on any date.
    """

    normalizer = NormalizationUtils
    custom_settings = {
        "USER_AGENT": (
            "Brasil.IO - Scraping para libertacao de dados da Covid 19 | "
            "Mais infos em: https://brasil.io/dataset/covid19/"
        ),
    }

    # Your spider should override these values
    state: State = None
    report_qualities: List[ReportQuality]

    # The information delay is the amount of days that the data collected by your scraper
    # is delayed in being published by the official source.
    # For example, a report from the day 20 may actually have the data referring to the day
    # 19, which means 1 day of information delay. If the data gathered by your scraper really
    # represents the numbers for the day when the bulletin was made available, keep this value 0.
    information_delay_in_days: int = 0

    def __init__(
        self,
        reports: Dict[datetime.date, FullReportModel],
        start_date: datetime.date = None,
        end_date: datetime.date = None,
        dates_range: List[datetime.date] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        if dates_range and (start_date or end_date):
            raise ValueError(
                "The parameter 'date_range' is not simultaneously supported with 'start_date' or 'end_date'."
            )

        self.today = datetime.date.today()
        if dates_range:
            self.dates_range = dates_range
            self.end_date = max(dates_range)
            self.start_date = min(dates_range)
        else:
            tomorrow = self.today + datetime.timedelta(days=1)
            self.end_date = (
                tomorrow if not end_date or end_date >= tomorrow else end_date
            )
            self.start_date = start_date if start_date else self.today
            self.dates_range = date_range(self.start_date, self.end_date)

        # The following variable is used to store the results of the scraping
        # so they can be used outside the spider - it will have one report per
        # date unless that report doesn't exist
        if reports is None:
            raise ValueError("'reports' must not be None")
        self.reports = reports

        self.pre_init()

    def add_new_bulletin_to_report(self, bulletin: BulletinModel, date: datetime.date):
        report = self.reports.get(date)
        if not report:
            report = FullReportModel(
                date=date - datetime.timedelta(days=self.information_delay_in_days),
                state=self.state,
                publishing_date=date,
                qualities=self.report_qualities,
            )
            self.reports[date] = report
        report.add_new_bulletin(bulletin)

    def pre_init(self) -> None:
        """
        You can [optionally] implement this method if you need to do something before the crawler starts
        """
