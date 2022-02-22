import datetime
from typing import Dict, List, Optional, Set

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
    undefined_or_imported_cases_bulletin: Optional[ImportedUndefinedBulletinModel]

    # we can fact check with lots of different sources
    _official_total_bulletins: List[StateTotalBulletinModel]
    _county_bulletins: Dict[int, CountyBulletinModel]
    _auto_calculated_total: StateTotalBulletinModel
    _expected_qualities: List
    _warnings: Set

    def __init__(self, reference_date, published_at, state, qualities):
        if not qualities:
            raise BadReportError("A report can't have no qualities.")
        self.reference_date = reference_date
        self.published_at = published_at
        self.state = state
        self._county_bulletins = {}
        self._warnings = set()
        self._expected_qualities = qualities
        self.undefined_or_imported_cases_bulletin = None
        self._official_total_bulletins = []
        self._auto_calculated_total = StateTotalBulletinModel(
            date=reference_date, state=state, source="Soma automática dos casos dos municípios"
        )
        self.undefined_or_imported_cases_bulletin = ImportedUndefinedBulletinModel(
            date=reference_date, state=state, source="Não encontrada"
        )

    def __repr__(self):
        return (
            f"FullReportModel("
            f"state={self.state.value}, "
            f"reference_date={self.reference_date.strftime('%d/%m/%Y')}, "
            f"published_at={self.published_at.strftime('%d/%m/%Y')}, "
            f"qtd_county_bulletins={len(self._county_bulletins)}, "
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
    def county_bulletins(self) -> List[CountyBulletinModel]:
        return list(self._county_bulletins.values())

    @property
    def has_undefined_or_imported_cases(self):
        return (
            bool(self.undefined_or_imported_cases_bulletin)
            and not self.undefined_or_imported_cases_bulletin.is_empty
        )

    def add_new_bulletin(self, bulletin: BulletinModel):
        if isinstance(bulletin, CountyBulletinModel):
            bulletin_key = hash(bulletin)
            existent_bulletin = self._pop_county_bulletin(bulletin_key)
            if existent_bulletin:
                bulletin = self._compare_county_bulletins_and_return_the_completest(
                    existent_bulletin, bulletin
                )
            self._county_bulletins[bulletin_key] = bulletin
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

    def add_warning(self, warning: str):
        """
        It takes a string formatted as a slug and saves it to use as a warning of something that
        didn't go well during the report assembly (such as missing data, data without validation, etc.).
        Use with moderation because all warnings are concatenated and used in the name of the state's csv
        and if this name gets too long it can be more of a hindrance than a help.
        """
        self._warnings.add(warning)

    @property
    def warnings_slug(self) -> str:
        self._auto_detect_warnings()
        if not self._warnings:
            return ""
        return "__" + "__".join(sorted(self._warnings))

    def _pop_county_bulletin(self, bulletin_key: int) -> Optional[CountyBulletinModel]:
        existent_bulletin = self._county_bulletins.pop(bulletin_key, None)
        if existent_bulletin:
            if existent_bulletin.has_confirmed_cases:
                self._auto_calculated_total.decrease_confirmed_cases(
                    existent_bulletin.confirmed_cases
                )
            if existent_bulletin.has_deaths:
                self._auto_calculated_total.decrease_deaths(existent_bulletin.deaths)
        return existent_bulletin

    def _compare_county_bulletins_and_return_the_completest(
        self, existent_bulletin: CountyBulletinModel, new_bulletin: CountyBulletinModel
    ) -> CountyBulletinModel:
        """
        It assumes that both the bulletins are from different sources and compare them to
        check if the sources has different values for the same data, if it does, we add a
        warning in the report.
        Returns the bulletin with more information or, if both the bulletins have incomplete data,
        returns a merged bulletin to get a completer one.
        """
        both_have_deaths = existent_bulletin.has_deaths and new_bulletin.has_deaths
        both_have_confirmed_cases = (
            existent_bulletin.has_confirmed_cases and new_bulletin.has_confirmed_cases
        )
        if existent_bulletin == new_bulletin:
            return existent_bulletin

        if (both_have_deaths and existent_bulletin.deaths != new_bulletin.deaths) or (
            both_have_confirmed_cases
            and existent_bulletin.confirmed_cases != new_bulletin.confirmed_cases
        ):
            self.add_warning("fontes-diferem-casos-municipios")

        if existent_bulletin.is_complete:
            return existent_bulletin
        if new_bulletin.is_complete:
            return new_bulletin
        existent_bulletin.merge_data(new_bulletin)
        return existent_bulletin

    def _auto_detect_warnings(self):
        if (
            ReportQuality.COUNTY_BULLETINS in self._expected_qualities
            and not self._county_bulletins
        ):
            self.add_warning(f"faltando-{ReportQuality.COUNTY_BULLETINS.value}")
        if (
            ReportQuality.UNDEFINED_OR_IMPORTED_CASES in self._expected_qualities
            and not self.has_undefined_or_imported_cases
        ):
            self.add_warning(
                f"faltando-{ReportQuality.UNDEFINED_OR_IMPORTED_CASES.value}"
            )
        if ReportQuality.ONLY_TOTAL in self._expected_qualities:
            self.add_warning(ReportQuality.ONLY_TOTAL.value)
            if not self.total_bulletin.has_confirmed_cases:
                self.add_warning("faltando-casos-confirmados")
            if not self.total_bulletin.has_deaths:
                self.add_warning("faltando-obitos")
        if not self._official_total_bulletins:
            self.add_warning("total-oficial-nao-considerado")
        elif not self._auto_calculated_total.is_empty and (
            not self.check_total_confirmed_cases() or not self.check_total_death_cases()
        ):
            self.add_warning("verificar-total")
