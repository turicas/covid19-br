import logging
import scrapy
from abc import ABC
from typing import Dict, List
from rows.utils.date import date_range
import datetime

from covid19br.common.constants import State
from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.common.models.full_report import FullReportModel, BulletinModel

logger = logging.getLogger(__name__)


class BaseCovid19Spider(scrapy.Spider, ABC):
    """
    Responsible for defining the interface with the crawler engine (scrapy)
    and the brasil.io backend.
    Knows how to gather the covid19 data for a state on any date.
    """

    normalizer = NormalizationUtils

    # Your spider should override this value
    state: State = None

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

        if dates_range:
            self.dates_range = dates_range
            self.end_date = max(dates_range)
            self.start_date = min(dates_range)
        else:
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)
            self.end_date = tomorrow if not end_date or end_date > tomorrow else today
            self.start_date = start_date if start_date else today
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
            report = FullReportModel(date=date, state=self.state)
            self.reports[date] = report
        report.add_new_bulletin(bulletin)

    def pre_init(self) -> None:
        """
        You can [optionally] implement this method if you need to do something before the crawler starts
        """
        pass
