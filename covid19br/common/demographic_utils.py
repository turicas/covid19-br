import rows
from functools import lru_cache
from pathlib import Path

from covid19br.common.constants import State

BASE_PATH = Path(__file__).parent.parent.parent


class DemographicUtils:

    population_data: list

    def __init__(self, year=2020):
        pop_csv_path = BASE_PATH / "covid19br" / "data" / f"populacao-por-municipio-{year}.csv"
        self.population_data = rows.import_from_csv(pop_csv_path)

    @lru_cache(maxsize=27)
    def get_cities_amount(self, state: State) -> int:
        """
        >>> DemographicUtils(2020).get_cities_amount(State.SP)
        645
        >>> DemographicUtils(2020).get_cities_amount(State.BA)
        417
        >>> DemographicUtils(2020).get_cities_amount(State.TO)
        139
        """
        return len(self.get_cities(state))

    @lru_cache(maxsize=27)
    def get_cities(self, state: State) -> list:
        return [city for city in self.population_data if city.state == state.value]
