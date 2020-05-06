from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import rows
from rows.utils import load_schema

DATA_PATH = Path(__file__).parent / "data"
SCHEMA_PATH = Path(__file__).parent / "schema"


def read_cases(input_filename, order_by=None):
    cases = rows.import_from_csv(
        input_filename, force_types=load_schema(str(SCHEMA_PATH / "caso.csv"))
    )
    if order_by:
        cases.order_by(order_by)
    return cases


def read_population():
    return rows.import_from_csv(
        DATA_PATH / "populacao-estimada-2019.csv",
        force_types=load_schema(str(SCHEMA_PATH / "populacao-estimada-2019.csv")),
    )


@lru_cache()
def read_epidemiological_week():
    filename = "data/epidemiological-week.csv"
    table = rows.import_from_csv(filename)
    return {row.date: row.epidemiological_week for row in table}


@lru_cache(maxsize=6000)
def epidemiological_week(date):
    return read_epidemiological_week()[date]


def get_data(input_filename):
    casos = read_cases(input_filename, order_by="date")
    dates = sorted(set(c.date for c in casos))
    row_key = lambda row: (row.place_type, row.state, row.city or None)
    caso_by_key = defaultdict(list)
    for caso in casos:
        caso_by_key[row_key(caso)].append(caso)
    for place_cases in caso_by_key.values():
        place_cases.sort(key=lambda row: row.date, reverse=True)

    brasil = read_population()
    city_by_key = {(city.state, city.city): city for city in brasil}
    population_by_state, place_keys = Counter(), []
    for city in brasil:
        population_by_state[city.state] += city.estimated_population
        place_keys.append(("city", city.state, city.city))
    place_code_by_state = {city.state: city.state_ibge_code for city in brasil}
    for state, place_code in place_code_by_state.items():
        place_keys.append(("state", state, None))
        place_keys.append(("city", state, "Importados/Indefinidos"))
    place_keys.sort()

    order_key = lambda row: row.order_for_place
    last_case_for_place = {}
    order_for_place = Counter()
    for date in dates:
        for place_key in place_keys:
            place_type, state, city = place_key
            place_cases = caso_by_key[place_key]
            valid_place_cases = sorted(
                [item for item in place_cases if item.date <= date],
                key=order_key,
                reverse=True,
            )
            if not valid_place_cases:
                # There are no cases for this city for this date - skip
                continue

            # This place has at least one case for this date (or before),
            # so use the newest one.
            last_valid_case = valid_place_cases[0]
            newest_case = place_cases[0]
            is_last = date == last_valid_case.date == newest_case.date
            order_for_place[place_key] += 1
            new_case = {
                "city": city,
                "city_ibge_code": last_valid_case.city_ibge_code,
                "date": date,
                "epidemiological_week": epidemiological_week(date),
                "estimated_population_2019": last_valid_case.estimated_population_2019,
                "is_last": is_last,
                "is_repeated": last_valid_case.date != date,
                "last_available_confirmed": last_valid_case.confirmed,
                "last_available_confirmed_per_100k_inhabitants": last_valid_case.confirmed_per_100k_inhabitants,
                "last_available_date": last_valid_case.date,
                "last_available_death_rate": last_valid_case.death_rate,
                "last_available_deaths": last_valid_case.deaths,
                "order_for_place": order_for_place[place_key],
                "place_type": place_type,
                "state": state,
            }

            last_case = last_case_for_place.get(place_key, None)
            if last_case is None:
                new_confirmed = new_case["last_available_confirmed"]
                new_deaths = new_case["last_available_deaths"]
            else:
                new_confirmed = (
                    new_case["last_available_confirmed"]
                    - last_case["last_available_confirmed"]
                )
                new_deaths = (
                    new_case["last_available_deaths"]
                    - last_case["last_available_deaths"]
                )
            new_case["new_confirmed"] = new_confirmed
            new_case["new_deaths"] = new_deaths
            last_case_for_place[place_key] = new_case

            yield new_case


if __name__ == "__main__":
    import argparse

    from tqdm import tqdm

    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in tqdm(get_data(args.input_filename)):
        writer.writerow(row)
