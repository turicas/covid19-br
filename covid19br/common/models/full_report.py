import datetime
from typing import Dict, List, Optional, Set

from covid19br.common.constants import State, ReportQuality
from covid19br.common.demographic_utils import DemographicUtils
from covid19br.common.exceptions import BadReportError
from covid19br.common.models.bulletin_models import (
    BulletinModel,
    CountyBulletinModel,
    ImportedUndefinedBulletinModel,
    StateTotalBulletinModel,
)
from covid19br.common.warnings import BulletinWarning, WarningType


class FullReportModel:
    """ "
    Represents a complete report for a given date (with city data
    + imported/undefined cases and the state's total consolidated).
    It has the domain of how to validate this data and standardize
    it to be consumed elsewhere in the application.
    """

    demographics = DemographicUtils()

    reference_date: datetime.date  # data date
    published_at: datetime.date  # bulletin date
    extraction_date: datetime.datetime
    state: State
    undefined_or_imported_cases_bulletin: Optional[ImportedUndefinedBulletinModel]

    # we can fact check with lots of different sources
    _official_total_bulletins: List[StateTotalBulletinModel]
    _county_bulletins: Dict[int, CountyBulletinModel]
    _auto_calculated_total: StateTotalBulletinModel
    _expected_qualities: List
    _warnings: Set[BulletinWarning]
    _notes: Set[str]

    def __init__(self, reference_date, published_at, state, qualities):
        if not qualities:
            raise BadReportError("A report can't have no qualities.")
        self.extraction_date = datetime.datetime.now()
        self.reference_date = reference_date
        self.published_at = published_at
        self.state = state
        self._county_bulletins = {}
        self._warnings = set()
        self._notes = set()
        self._expected_qualities = qualities
        self.undefined_or_imported_cases_bulletin = None
        self._official_total_bulletins = []
        self._auto_calculated_total = StateTotalBulletinModel(
            date=reference_date, state=state, source="Soma automática"
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
            for official_bulletin in self._official_total_bulletins:
                if official_bulletin.is_complete:
                    return official_bulletin
        return self._auto_calculated_total

    @property
    def county_bulletins(self) -> List[CountyBulletinModel]:
        county_bulletins = self._county_bulletins.values()
        bulletins_qt = len(county_bulletins)
        expected_bulletins_qt = self.demographics.get_cities_amount(self.state)
        if bulletins_qt == expected_bulletins_qt:
            return list(county_bulletins)
        missing_bulletins = self._get_missing_bulletins()
        if ReportQuality.ONLY_TOTAL not in self._expected_qualities:
            for bulletin in missing_bulletins:
                self.add_note(
                    f"A cidade {bulletin.city} não foi encontrada pelo raspador, "
                    f"então foi dado que o valor de óbitos e casos para ela é zero."
                )
        return [*self._county_bulletins.values(), *missing_bulletins]

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
            rows.append(bulletin.to_csv_row())
        rows.append(self.undefined_or_imported_cases_bulletin.to_csv_row())
        rows.append(self.total_bulletin.to_csv_row())
        return rows

    def export_metadata_in_csv(self):
        total_bulletin = self.total_bulletin
        return {
            "data_boletim": self.published_at.strftime("%Y-%m-%d"),
            "data_coleta": self.extraction_date.strftime("%d/%m/%Y %H:%M:%S"),
            "state": self.state.value,
            "data_dados": self.reference_date.strftime("%Y-%m-%d"),
            "confirmed": total_bulletin.confirmed_cases,
            "deaths": total_bulletin.deaths,
            "FONTES": self.sources,
        }

    def export_metadata_in_text(self):
        total_bulletin = self.total_bulletin

        resp = [
            f"{self.reference_date.strftime('%Y-%m-%d')} COVID-19 {self.state.value}",
            f"Data do boletim..: {self.published_at.strftime('%Y-%m-%d')}",
            f"Data dos dados...: {self.reference_date.strftime('%Y-%m-%d')}",
            f"Data da coleta...: {self.extraction_date.strftime('%d/%m/%Y %H:%M:%S')}\n",
            f"Qtd casos confirmados.: {total_bulletin.confirmed_cases}",
            f"Qtd casos de óbitos...: {total_bulletin.deaths}",
            "\nFONTES:",
            f"{self.sources}",
        ]

        if self._warnings:
            resp.append("\nWARNINGS:")
            for warning in self._warnings:
                description = "\n\t".join(warning.description.split("\n"))
                resp.append(f"- {warning.slug}:\n\t{description}")

        if self._notes:
            resp.append("\nNOTAS:")
            resp.append("\n- ".join(self._notes))

        resp.append("\n" + "-" * 20)
        return "\n".join(resp)

    def add_note(self, note: str):
        """
        It saves notes to inform humans about important things that happened during the report assembly.
        """
        self._notes.add(note)

    def add_warning(self, slug: WarningType, description: str = None):
        """
        It saves warnings of things that didn't go well during the report assembly (such as missing data,
        data without validation, etc.). Use with moderation because all warnings are concatenated and used
        in the name of the state's csv and if this name gets too long it can be more of a hindrance than a help.
        If the thing you want to inform is not critical, use the method add_note instead :)
        """
        warning = BulletinWarning(slug.value, description)
        self._warnings.add(warning)

    @property
    def warnings_slug(self) -> str:
        self._auto_detect_warnings()
        if not self._warnings:
            return ""
        warnings = set([w.slug for w in self._warnings])
        return "__" + "__".join(sorted(warnings))

    @property
    def sources(self) -> str:
        sources = []
        for bulletin in self._official_total_bulletins:
            bulletin_source = " | ".join(sorted(bulletin.sources))
            sources.append(f"- Total oficial: {bulletin_source}")

        county_sources = set()
        for bulletin in self._county_bulletins.values():
            county_sources.update(bulletin.sources)
        if self.has_undefined_or_imported_cases:
            county_sources.update(self.undefined_or_imported_cases_bulletin.sources)
        for source in county_sources:
            sources.append(f"- Fonte municipios: {source}")

        return "\n".join(sources) or "-"

    def _get_missing_bulletins(self) -> List[CountyBulletinModel]:
        all_cities = self.demographics.get_cities(self.state)
        existent_cities = [
            bulletin.city for bulletin in self._county_bulletins.values()
        ]
        resp = []
        for city in all_cities:
            city_name = city.city
            if city.city not in existent_cities:
                resp.append(
                    CountyBulletinModel(
                        date=self.published_at,
                        state=self.state,
                        city=city_name,
                        source="Não encontrado",
                    )
                )
        return resp

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
            self.add_warning(
                WarningType.SOURCES_DONT_MATCH,
                description=(
                    "Valor de casos/óbitos dos municípios inconsistente entre as duas fontes de dados.\n"
                    f"Fonte 1: {existent_bulletin.sources}\n"
                    f"Fonte 2: {new_bulletin.sources}"
                ),
            )

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
            self.add_warning(
                WarningType.MISSING_COUNTY_BULLETINS,
                description=(
                    "A raspagem de dados por município está implementada para esse estado, "
                    "porém algo deu errado e não foi possível encontrar os dados."
                ),
            )
        if (
            ReportQuality.UNDEFINED_OR_IMPORTED_CASES in self._expected_qualities
            and not self.has_undefined_or_imported_cases
        ):
            self.add_warning(
                WarningType.MISSING_IMPORTED_UNDEFINED_CASES,
                description=(
                    "É esperado que esse scraping consiga identificar os casos importados/indefinidos, "
                    "porém algo deu errado e não foi possível encontrar os dados."
                ),
            )
        if ReportQuality.ONLY_TOTAL in self._expected_qualities:
            self.add_warning(
                WarningType.ONLY_TOTAL,
                description="Apenas a raspagem do total foi implementada por enquanto.",
            )
        if not self.total_bulletin.has_confirmed_cases:
            self.add_warning(
                WarningType.MISSING_CONFIRMED_CASES,
                description=(
                    "Algo deu errado e não foi possível raspar a quantidade de casos confirmados.\n"
                    "Confirmar se houve alguma mudança na disponibilização do dado e se o raspador "
                    "deve ser atualizado."
                ),
            )
        if not self.total_bulletin.has_deaths:
            self.add_warning(
                WarningType.MISSING_DEATHS,
                description=(
                    "Algo deu errado e não foi possível raspar a quantidade de casos confirmados.\n"
                    "Confirmar se houve alguma mudança na disponibilização do dado e se o raspador "
                    "deve ser atualizado."
                ),
            )
        if not self._official_total_bulletins:
            self.add_warning(
                WarningType.NO_OFFICIAL_TOTAL,
                description=(
                    "Os dados totais do .csv não foram validados em fontes oficiais, "
                    "são apenas a soma automática dos dados dos municípios."
                ),
            )
        elif not self._auto_calculated_total.is_empty and (
            not self.check_total_confirmed_cases() or not self.check_total_death_cases()
        ):
            sources_data = "\n".join(
                [
                    f"Fonte {{ {' | '.join(bulletin.sources)} }}: "
                    f"{bulletin.confirmed_cases} confirmados e {bulletin.deaths} óbitos."
                    for bulletin in self._official_total_bulletins
                ]
            )
            self.add_warning(
                WarningType.TOTAL_DONT_MATCH,
                description=(
                    "A soma automática do total de casos e mortes por municípios não bate com o total "
                    "disponibilizado por fontes oficiais.\n"
                    f"Fonte soma automática: "
                    f"{self._auto_calculated_total.confirmed_cases} confirmados "
                    f"e {self._auto_calculated_total.deaths} óbitos.\n"
                    f"{sources_data}"
                ),
            )
