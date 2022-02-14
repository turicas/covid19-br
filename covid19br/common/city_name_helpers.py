import rows
from rows.fields import slug
from functools import lru_cache
from fuzzy_types import FuzzyDict
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
POPULATION_PATH = BASE_PATH / "covid19br" / "data" / "populacao-por-municipio-2020.csv"


@lru_cache()
def brazilian_population():
    return rows.import_from_csv(POPULATION_PATH)


@lru_cache(maxsize=27)
def state_population(state):
    return [row for row in brazilian_population() if row.state == state]


@lru_cache(maxsize=6000)
def _normalize_city_name(city):
    city = slug(city)

    for word in ("da", "das", "de", "do", "dos"):
        city = city.replace(f"_{word}_", "_")

    return city


@lru_cache(maxsize=900)
def _city_id_from_name(state):
    data = {row.city: int(row.city_ibge_code) for row in state_population(state)}
    data["Importados/Indefinidos"] = None
    return data


@lru_cache(maxsize=900)
def _get_city_id_from_name(state, name):
    normalized_cities = FuzzyDict({
        _normalize_city_name(key): value
        for key, value in _city_id_from_name(state).items()
    })
    return normalized_cities[_normalize_city_name(name)]


@lru_cache(maxsize=27)
def _city_name_from_id(state):
    return {value: key for key, value in _city_id_from_name(state).items()}


@lru_cache(maxsize=5570)
def _get_city_name_from_id(state, city_id):
    return _city_name_from_id(state)[city_id]


def fix_city_name(state, city):
    try:
        city_id = _get_city_id_from_name(state, city)
        city_name = _get_city_name_from_id(state, city_id)
    except KeyError:
        raise ValueError(f"Unknown city '{city}' for state {state}")
    else:
        return city_name
