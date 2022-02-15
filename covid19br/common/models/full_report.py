import datetime
from typing import List, Optional

from covid19br.common.constants import NOT_INFORMED_CODE, State, ReportQuality
from covid19br.common.exceptions import BadReportError
from covid19br.common.models.bulletin_models import (
    BulletinModel,
    CountyBulletinModel,
    ImportedUndefinedBulletinModel,
    StateTotalBulletinModel,
)


class FullReportModel:
    """ "
    Represents a complete report for a given date (with city data
    + imported/undefined cases and the state's total consolidated).
    It has the domain of how to validate this data and standardize
    it to be consumed elsewhere in the application.
    """

    date: datetime.date
    publishing_date: datetime.date
    state: State
    county_bulletins: List[CountyBulletinModel]
    undefined_or_imported_cases_bulletin: Optional[ImportedUndefinedBulletinModel]
    total_bulletin: StateTotalBulletinModel

    _auto_calculate_total = True
    _expected_qualities = []

    def __init__(self, date, publishing_date, state, qualities):
        if not qualities:
            raise BadReportError("A report can't have no qualities.")
        self.date = date
        self.publishing_date = publishing_date
        self.state = state
        self.county_bulletins = []
        self._expected_qualities = qualities
        self.undefined_or_imported_cases_bulletin = None
        self.total_bulletin = StateTotalBulletinModel(
            date=date, state=state, source_url="auto computed"
        )

    def __repr__(self):
        return (
            f"FullReportModel("
            f"state={self.state.value}, "
            f"date={self.date.strftime('%d/%m/%Y')}, "
            f"publishing_date={self.publishing_date.strftime('%d/%m/%Y')}, "
            f"qtd_county_bulletins={len(self.county_bulletins)}, "
            f"has_undefined_or_imported_cases={self.has_undefined_or_imported_cases}, "
            f"total_deaths={self.total_bulletin.deaths}, "
            f"total_confirmed_cases={self.total_bulletin.confirmed_cases}"
            f")"
        )

    @property
    def has_undefined_or_imported_cases(self):
        return (
            bool(self.undefined_or_imported_cases_bulletin)
            and self.undefined_or_imported_cases_bulletin.has_confirmed_cases_and_deaths
        )

    def add_new_bulletin(self, bulletin: BulletinModel):
        if isinstance(bulletin, CountyBulletinModel):
            self.county_bulletins.append(bulletin)
        elif isinstance(bulletin, ImportedUndefinedBulletinModel):
            if self.undefined_or_imported_cases_bulletin:
                raise ValueError(
                    "undefined_or_imported_cases_bulletin was already set in this report."
                )
            self.undefined_or_imported_cases_bulletin = bulletin
        elif isinstance(bulletin, StateTotalBulletinModel):
            self.total_bulletin = bulletin
            self._auto_calculate_total = False
            return
        else:
            return

        if self._auto_calculate_total:
            if (
                bulletin.confirmed_cases is not None
                and bulletin.confirmed_cases != NOT_INFORMED_CODE
            ):
                self.total_bulletin.increase_confirmed_cases(bulletin.confirmed_cases)
            if bulletin.deaths is not None and bulletin.deaths != NOT_INFORMED_CODE:
                self.total_bulletin.increase_deaths(bulletin.deaths)

    def check_total_death_cases(self, expected_amount, raise_error=True) -> bool:
        cases_match = self.total_bulletin.deaths == expected_amount
        if not cases_match and raise_error:
            raise BadReportError(
                f"Expected {expected_amount} death cases, but got {self.total_bulletin} instead."
            )
        return cases_match

    def check_total_confirmed_cases(self, expected_amount, raise_error=True) -> bool:
        cases_match = self.total_bulletin.confirmed_cases == expected_amount
        if not cases_match and raise_error:
            raise BadReportError(
                f"Expected {expected_amount} confirmed cases, but got {self.total_bulletin} instead."
            )
        return cases_match

    def to_csv_rows(self):
        rows = []
        for bulletin in sorted(self.county_bulletins, key=lambda x: x.city):
            if bulletin.has_confirmed_cases_and_deaths:
                rows.append(bulletin.to_csv_row())
        if self.has_undefined_or_imported_cases:
            rows.append(self.undefined_or_imported_cases_bulletin.to_csv_row())
        rows.append(self.total_bulletin.to_csv_row())
        return rows

    @property
    def warnings_slug(self) -> str:
        warnings = []
        if ReportQuality.COUNTY_BULLETINS in self._expected_qualities and not self.county_bulletins:
            warnings.append(f'faltando-{ReportQuality.COUNTY_BULLETINS.value}')
        if ReportQuality.UNDEFINED_OR_IMPORTED_CASES in self._expected_qualities and not self.has_undefined_or_imported_cases:
            warnings.append(f'faltando-{ReportQuality.UNDEFINED_OR_IMPORTED_CASES.value}')
        if ReportQuality.ONLY_TOTAL in self._expected_qualities:
            warnings.append(ReportQuality.ONLY_TOTAL.value)
            if not self.total_bulletin.has_confirmed_cases:
                warnings.append("faltando-casos-confirmados")
            if not self.total_bulletin.has_deaths:
                warnings.append("faltando-obitos")

        if not warnings:
            return ""
        return "__" + "__".join(warnings)
