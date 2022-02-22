import datetime
from abc import ABC
from typing import Set

from covid19br.common.city_name_helpers import fix_city_name
from covid19br.common.constants import NOT_INFORMED_CODE, PlaceType, State
from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.common.exceptions import BadReportError


class BulletinModel(ABC):
    """
    Represents a line of the csv generated in a status report.
    It has the number of cases/deaths reported for a single city
    or total in the state.
    """

    date: datetime.date
    sources: Set[str]
    place_type: PlaceType
    state: State
    confirmed_cases: int
    deaths: int
    notes: str

    def __init__(
        self,
        date,
        source,
        place_type,
        state,
        confirmed_cases=None,
        deaths=None,
        notes=None,
    ):
        if not date:
            raise BadReportError("date field is required in a report.")
        if not source:
            raise BadReportError("source field is required in a report.")
        if not place_type:
            raise BadReportError("place_type field is required in a report.")
        self._check_state_or_raise_error(state)
        self.state = state
        self.set_confirmed_cases_value(confirmed_cases)
        self.set_deaths_value(deaths)
        self.date = date
        self.sources = {source}
        self.place_type = place_type
        self.notes = notes

    @staticmethod
    def _check_state_or_raise_error(state):
        if not state:
            raise BadReportError("state field is required in a report.")

    def set_confirmed_cases_value(self, confirmed_cases):
        try:
            cases_number = NormalizationUtils.ensure_integer(confirmed_cases)
            self.confirmed_cases = (
                cases_number if cases_number or cases_number == 0 else NOT_INFORMED_CODE
            )
        except ValueError:
            raise BadReportError(
                f"Invalid value for confirmed_cases: '{confirmed_cases}'. Value can't be cast to int."
            )

    def set_deaths_value(self, deaths):
        try:
            cases_number = NormalizationUtils.ensure_integer(deaths)
            self.deaths = (
                cases_number if cases_number or cases_number == 0 else NOT_INFORMED_CODE
            )
        except ValueError:
            raise BadReportError(
                f"Invalid value for deaths: '{deaths}'. Value can't be cast to int."
            )

    @property
    def is_empty(self) -> bool:
        return not self.has_deaths and not self.has_confirmed_cases

    @property
    def is_complete(self) -> bool:
        return self.has_deaths and self.has_confirmed_cases

    @property
    def has_deaths(self) -> bool:
        return self.deaths and self.deaths != NOT_INFORMED_CODE

    @property
    def has_confirmed_cases(self) -> bool:
        return self.confirmed_cases and self.confirmed_cases != NOT_INFORMED_CODE

    def to_csv_row(self):
        raise NotImplementedError()


class StateTotalBulletinModel(BulletinModel):
    def __init__(self, date, source, state, *args, **kwargs):
        super().__init__(
            date=date,
            source=source,
            place_type=PlaceType.STATE,
            state=state,
            *args,
            **kwargs,
        )

    def __repr__(self):
        return (
            f"StateTotalBulletinModel("
            f"date={self.date.strftime('%d/%m/%Y')}, "
            f"state={self.state.value}, "
            f"qtd_confirmed_cases={self.confirmed_cases}, "
            f"qtd_deaths={self.deaths}"
            f")"
        )

    def increase_deaths(self, value: int):
        value = NormalizationUtils.ensure_integer(value)
        if self.deaths == NOT_INFORMED_CODE:
            self.deaths = value
            return
        self.deaths += value

    def increase_confirmed_cases(self, value: int):
        value = NormalizationUtils.ensure_integer(value)
        if self.confirmed_cases == NOT_INFORMED_CODE:
            self.confirmed_cases = value
            return
        self.confirmed_cases += value

    def decrease_deaths(self, value: int):
        value = NormalizationUtils.ensure_integer(value)
        self.deaths -= value
        if self.deaths < 0:
            self.deaths = NOT_INFORMED_CODE

    def decrease_confirmed_cases(self, value: int):
        value = NormalizationUtils.ensure_integer(value)
        self.confirmed_cases -= value
        if self.confirmed_cases < 0:
            self.confirmed_cases = NOT_INFORMED_CODE

    def to_csv_row(self):
        cases = self.confirmed_cases if self.confirmed_cases != NOT_INFORMED_CODE else 0
        deaths = self.deaths if self.deaths != NOT_INFORMED_CODE else 0
        return {"municipio": "TOTAL NO ESTADO", "confirmados": cases, "mortes": deaths}


class CountyBulletinModel(BulletinModel):
    city: str

    def __init__(self, date, source, state, city, *args, **kwargs):
        if not city:
            raise BadReportError("city field is required in a county report.")
        self._check_state_or_raise_error(state)
        self.city = fix_city_name(state.value, city)
        super().__init__(
            date=date,
            source=source,
            place_type=PlaceType.CITY,
            state=state,
            *args,
            **kwargs,
        )

    def __repr__(self):
        return (
            f"CountyBulletinModel("
            f"date={self.date.strftime('%d/%m/%Y')}, "
            f"state={self.state.value}, "
            f"city={self.city}, "
            f"qtd_confirmed_cases={self.confirmed_cases}, "
            f"qtd_deaths={self.deaths}"
            f")"
        )

    def __eq__(self, other):
        """
        Overrides the default implementation to better check if two
        CountyBulletins have the same data (even if from different sources)
        """
        if isinstance(other, self.__class__):
            return (
                self.state == other.state
                and self.city == other.city
                and self.date == other.date
                and self.deaths == other.deaths
                and self.confirmed_cases == other.confirmed_cases
            )
        else:
            return False

    def __hash__(self):
        """
        Overrides the default implementation to faster lookup for
        CountyBulletins for the same city in the same date.
        """
        return hash((self.state, self.city, self.date))

    def to_csv_row(self):
        cases = self.confirmed_cases if self.confirmed_cases != NOT_INFORMED_CODE else 0
        deaths = self.deaths if self.deaths != NOT_INFORMED_CODE else 0
        return {"municipio": self.city, "confirmados": cases, "mortes": deaths}

    def merge_data(self, other):
        if isinstance(other, self.__class__) and hash(self) == hash(other):
            if not self.has_deaths and other.has_deaths:
                self.deaths = other.deaths
                self.sources.update(other.sources)
            if not self.has_confirmed_cases and other.has_confirmed_cases:
                self.confirmed_cases = other.confirmed_cases
                self.sources.update(other.sources)


class ImportedUndefinedBulletinModel(BulletinModel):
    def __init__(self, date, source, state, *args, **kwargs):
        super().__init__(
            date=date,
            source=source,
            place_type=PlaceType.CITY,
            state=state,
            *args,
            **kwargs,
        )

    def __repr__(self):
        return (
            f"ImportedUndefinedBulletinModel("
            f"date={self.date.strftime('%d/%m/%Y')}, "
            f"state={self.state.value}, "
            f"qtd_confirmed_cases={self.confirmed_cases}, "
            f"qtd_deaths={self.deaths}"
            f")"
        )

    def to_csv_row(self):
        cases = self.confirmed_cases if self.confirmed_cases != NOT_INFORMED_CODE else 0
        deaths = self.deaths if self.deaths != NOT_INFORMED_CODE else 0
        return {
            "municipio": "Importados/Indefinidos",
            "confirmados": cases,
            "mortes": deaths,
        }
