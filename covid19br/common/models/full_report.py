import datetime
from typing import List, Optional

from covid19br.common.constants import State, ReportQuality
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

    reference_date: datetime.date  # data date
    published_at: datetime.date  # bulletin date
    state: State
    county_bulletins: List[CountyBulletinModel]
    undefined_or_imported_cases_bulletin: Optional[ImportedUndefinedBulletinModel]

    # we can fact check with lots of different sources
    _official_total_bulletins: List[StateTotalBulletinModel]
    _auto_calculated_total: StateTotalBulletinModel
    _expected_qualities: List

    def __init__(self, reference_date, published_at, state, qualities):
        if not qualities:
            raise BadReportError("A report can't have no qualities.")
        self.reference_date = reference_date
        self.published_at = published_at
        self.state = state
        self.county_bulletins = []
        self._expected_qualities = qualities
        self.undefined_or_imported_cases_bulletin = None
        self._official_total_bulletins = []
        self._auto_calculated_total = StateTotalBulletinModel(
            date=reference_date, state=state, source_url="auto computed"
        )
        self.undefined_or_imported_cases_bulletin = ImportedUndefinedBulletinModel(
            date=reference_date, state=state, source_url="not found"
        )

    def __repr__(self):
        return (
            f"FullReportModel("
            f"state={self.state.value}, "
            f"reference_date={self.reference_date.strftime('%d/%m/%Y')}, "
            f"published_at={self.published_at.strftime('%d/%m/%Y')}, "
            f"qtd_county_bulletins={len(self.county_bulletins)}, "
            f"has_undefined_or_imported_cases={self.has_undefined_or_imported_cases}, "
            f"total_deaths={self.total_bulletin.deaths}, "
            f"total_confirmed_cases={self.total_bulletin.confirmed_cases}"
            f")"
        )

    @property
    def total_bulletin(self) -> StateTotalBulletinModel:
        if self._official_total_bulletins:
            return self._official_total_bulletins[0]
        return self._auto_calculated_total

    @property
    def has_undefined_or_imported_cases(self):
        return (
            bool(self.undefined_or_imported_cases_bulletin)
            and not self.undefined_or_imported_cases_bulletin.is_empty
        )

    def add_new_bulletin(self, bulletin: BulletinModel):
        if isinstance(bulletin, CountyBulletinModel):
            self.county_bulletins.append(bulletin)
        elif isinstance(bulletin, ImportedUndefinedBulletinModel):
            self.undefined_or_imported_cases_bulletin = bulletin
        elif isinstance(bulletin, StateTotalBulletinModel):
            if not bulletin.is_empty:
                self._official_total_bulletins.append(bulletin)
            return
        else:
            return

        if bulletin.has_confirmed_cases:
            self._auto_calculated_total.increase_confirmed_cases(
                bulletin.confirmed_cases
            )
        if bulletin.has_deaths:
            self._auto_calculated_total.increase_deaths(bulletin.deaths)

    def check_total_death_cases(self) -> bool:
        if not self._official_total_bulletins:
            return False
        auto_calculated_deaths = self._auto_calculated_total.deaths
        return all(
            [
                auto_calculated_deaths == official_bulletin.deaths
                for official_bulletin in self._official_total_bulletins
            ]
        )

    def check_total_confirmed_cases(self) -> bool:
        if not self._official_total_bulletins:
            return False
        auto_calculated_cases = self._auto_calculated_total.confirmed_cases
        return all(
            [
                auto_calculated_cases == official_bulletin.confirmed_cases
                for official_bulletin in self._official_total_bulletins
            ]
        )

    def to_csv_rows(self):
        rows = []
        for bulletin in sorted(self.county_bulletins, key=lambda x: x.city):
            if not bulletin.is_empty:
                rows.append(bulletin.to_csv_row())
        rows.append(self.undefined_or_imported_cases_bulletin.to_csv_row())
        rows.append(self.total_bulletin.to_csv_row())
        return rows

    @property
    def warnings_slug(self) -> str:
        warnings = []
        if (
            ReportQuality.COUNTY_BULLETINS in self._expected_qualities
            and not self.county_bulletins
        ):
            warnings.append(f"faltando-{ReportQuality.COUNTY_BULLETINS.value}")
        if (
            ReportQuality.UNDEFINED_OR_IMPORTED_CASES in self._expected_qualities
            and not self.has_undefined_or_imported_cases
        ):
            warnings.append(
                f"faltando-{ReportQuality.UNDEFINED_OR_IMPORTED_CASES.value}"
            )
        if ReportQuality.ONLY_TOTAL in self._expected_qualities:
            warnings.append(ReportQuality.ONLY_TOTAL.value)
            if not self.total_bulletin.has_confirmed_cases:
                warnings.append("faltando-casos-confirmados")
            if not self.total_bulletin.has_deaths:
                warnings.append("faltando-obitos")
        if not self._official_total_bulletins:
            warnings.append("total-oficial-nao-considerado")
        elif not self._auto_calculated_total.is_empty and (
            not self.check_total_confirmed_cases() or not self.check_total_death_cases()
        ):
            warnings.append("verificar-total")

        if not warnings:
            return ""
        return "__" + "__".join(warnings)
