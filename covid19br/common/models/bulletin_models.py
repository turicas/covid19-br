import datetime
from abc import ABC

from covid19br.common.constants import PlaceType, NOT_INFORMED_CODE, State, IMPORTED_OR_UNDEFINED_CODE
from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.common.exceptions import BadReportError


class BulletinModel(ABC):
    """
    Represents a line of the csv generated in a status report.
    It has the number of cases/deaths reported for a single city
    or total in the state.
    """
    date: datetime.date
    source_url: str
    place_type: PlaceType
    state: State
    city: str
    confirmed_cases: int
    deaths: int
    notes: str

    def __init__(self, date, source_url, place_type, state, city=None, confirmed_cases=None, deaths=None, notes=None):
        if not date:
            raise BadReportError('date field is required in a report.')
        if not source_url:
            raise BadReportError('source_url field is required in a report.')
        if not place_type:
            raise BadReportError('place_type field is required in a report.')
        if not state:
            raise BadReportError('state field is required in a report.')
        self.set_confirmed_cases_value(confirmed_cases)
        self.set_deaths_value(deaths)
        self.date = date
        self.source_url = source_url
        self.place_type = place_type
        self.state = state
        self.city = city
        self.notes = notes

    def set_confirmed_cases_value(self, confirmed_cases):
        try:
            self.confirmed_cases = NormalizationUtils.ensure_integer(confirmed_cases) or NOT_INFORMED_CODE
        except ValueError:
            raise BadReportError(f"Invalid value for confirmed_cases: '{confirmed_cases}'. Value can't be cast to int.")

    def set_deaths_value(self, deaths):
        try:
            self.deaths = NormalizationUtils.ensure_integer(deaths) or NOT_INFORMED_CODE
        except ValueError:
            raise BadReportError(f"Invalid value for deaths: '{deaths}'. Value can't be cast to int.")

    @property
    def has_confirmed_cases_or_deaths(self) -> bool:
        return self.confirmed_cases != NOT_INFORMED_CODE and self.deaths != NOT_INFORMED_CODE


class StateTotalBulletinModel(BulletinModel):
    def __init__(self, date, source_url, state, *args, **kwargs):
        super().__init__(date=date, source_url=source_url, place_type=PlaceType.STATE, state=state, *args, **kwargs)

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
        self.deaths += value

    def increase_confirmed_cases(self, value: int):
        self.confirmed_cases += value


class CountyBulletinModel(BulletinModel):
    def __init__(self, date, source_url, state, city, *args, **kwargs):
        # todo ->  normalizar nome + verificar se cidade existe
        if not city:
            raise BadReportError('city field is required in a county report.')
        super().__init__(
            date=date,
            source_url=source_url,
            place_type=PlaceType.CITY,
            state=state,
            city=city,
            *args, **kwargs,
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


class ImportedUndefinedBulletinModel(BulletinModel):
    def __init__(self, date, source_url, state, *args, **kwargs):
        super().__init__(
            date=date,
            source_url=source_url,
            place_type=PlaceType.CITY,
            state=state,
            city=IMPORTED_OR_UNDEFINED_CODE,
            *args, **kwargs,
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
