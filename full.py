from collections import Counter, defaultdict
from pathlib import Path

import rows
from rows.utils import load_schema


DATA_PATH = Path(__file__).parent / "data"
SCHEMA_PATH = Path(__file__).parent / "schema"


def get_data(input_filename):
    casos = rows.import_from_csv(
        input_filename, force_types=load_schema(str(SCHEMA_PATH / "caso.csv"))
    )
    casos.order_by("date")
    dates = sorted(set(c.date for c in casos))
    row_key = lambda row: (row.place_type, row.state, row.city)
    caso_by_key = defaultdict(list)
    for caso in casos:
        caso_by_key[row_key(caso)].append(caso)

    brasil = rows.import_from_csv(
        DATA_PATH / "populacao-estimada-2019.csv",
        force_types=load_schema(str(SCHEMA_PATH / "populacao-estimada-2019.csv")),
    )
    population_by_city = defaultdict(lambda: None)
    population_by_state, place_keys = Counter(), []
    place_code_by_city = defaultdict(lambda: None)
    for city in brasil:
        population_by_city[(city.state, city.city)] = city.estimated_population
        place_code_by_city[(city.state, city.city)] = city.city_ibge_code
        population_by_state[city.state] += city.estimated_population
        place_keys.append(("city", city.state, city.city))
    states = {city.state: city.state_ibge_code for city in brasil}
    place_code_by_state = defaultdict(lambda: None)
    for state, place_code in states.items():
        place_keys.append(("state", state, None))
        place_keys.append(("city", state, "Importados/Indefinidos"))
        place_code_by_state[state] = place_code
    place_keys.sort()

    order_key = lambda row: row.order_for_place
    last_date = dates[-1]
    last_case_for_place = {}
    for date in dates:
        for place_key in place_keys:
            last_case = last_case_for_place.get(place_key, None)
            place_type, state, city = place_key
            place_cases = caso_by_key[place_key]
            place_cases.sort(key=lambda row: row.date, reverse=True)
            valid_place_cases = sorted(
                [
                    item
                    for item in place_cases
                    if item.date <= date
                ],
                key=order_key,
                reverse=True
            )
            if valid_place_cases:
                # This place has at least one case for this date (or before),
                # so use the newest one.
                last_valid_case = valid_place_cases[0]
                newest_case = place_cases[0]
                new_case = {
                    "city": city,
                    "city_ibge_code": last_valid_case.city_ibge_code,
                    "date": date,
                    "estimated_population_2019": last_valid_case.estimated_population_2019,
                    "is_fake": last_valid_case.date != date,
                    "is_last": date == last_valid_case.date == newest_case.date,
                    "last_available_confirmed": last_valid_case.confirmed,
                    "last_available_confirmed_per_100k_inhabitants": last_valid_case.confirmed_per_100k_inhabitants,
                    "last_available_date": last_valid_case.date,
                    "last_available_death_rate": last_valid_case.death_rate,
                    "last_available_deaths": last_valid_case.deaths,
                    "place_type": place_type,
                    "state": state,
                }
            else:
                if place_cases:
                    newest_case = place_cases[0]
                    is_last = date == newest_case.date
                else:
                    is_last = date == last_date
                if place_type == "state":
                    population = population_by_state[state]
                    place_code = place_code_by_state[state]
                elif place_type == "city":
                    population = population_by_city[(state, city)]
                    place_code = place_code_by_city[(state, city)]
                else:
                    raise ValueError(f"Unknown place type: {repr(place_type)}")

                new_case = {
                    "city": city,
                    "city_ibge_code": place_code,
                    "date": date,
                    "estimated_population_2019": population,
                    "is_last": is_last,
                    "is_fake": False,
                    "last_available_confirmed": None,
                    "last_available_confirmed_per_100k_inhabitants": None,
                    "last_available_date": None,
                    "last_available_death_rate": None,
                    "last_available_deaths": None,
                    "place_type": place_type,
                    "state": state,
                }
            if last_case is None:
                new_confirmed = 0
                new_deaths = 0
            else:
                last_confirmed = last_case["last_available_confirmed"]
                new_confirmed = new_case["last_available_confirmed"]
                new_confirmed = (new_confirmed or 0) - (last_confirmed or 0)
                last_deaths = last_case["last_available_deaths"]
                new_deaths = new_case["last_available_deaths"]
                new_deaths = (new_deaths or 0) - (last_deaths or 0)
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
