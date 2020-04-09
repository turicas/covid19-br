from collections import Counter, defaultdict
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


def get_data(input_filename):
    casos = read_cases(input_filename, order_by="date")
    dates = sorted(set(c.date for c in casos))
    row_key = lambda row: (row.place_type, row.state, row.city)
    caso_by_key = defaultdict(list)
    for caso in casos:
        caso_by_key[row_key(caso)].append(caso)

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
    last_date = dates[-1]
    last_case_for_place, had_cases = {}, {}
    for date in dates:
        # TODO: faltam os dados (novos casos, novas mortes, last_xxx) para
        # place_type = 'state'
        # TODO: São Paulo (município) aparece com 1 caso na data 2020-02-25 em
        # last_available_confirmed. No entanto, new_confirmed aparece como 0.
        # Não deveria ser 1, já que foi o primeiro caso confirmado?
        # TODO: adicionar coluna "day_number_for_place", que
        # começa em 1 na data em que casos passa a ser maior que 0
        # TODO: decidir o que fazer com day_number_for_place quando número de
        # casos voltar a 0 (remanejamento de casos).
        # TODO: detalhar que valores new_confirmed e new_deaths podem ser
        # negativos.
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
                    "is_repeated": last_valid_case.date != date,
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
                    city_row = city_by_key.get((state, city), None)
                    if city_row is None:
                        if city != "Importados/Indefinidos":
                            raise ValueError(f"City {city} not found")
                        population = place_code = None
                    else:
                        population = city_row.estimated_population
                        place_code = city_row.city_ibge_code
                else:
                    raise ValueError(f"Unknown place type: {repr(place_type)}")

                new_case = {
                    "city": city,
                    "city_ibge_code": place_code,
                    "date": date,
                    "estimated_population_2019": population,
                    "is_last": is_last,
                    "is_repeated": False,
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
            place_had_cases = had_cases.get(place_key, False)
            if not place_had_cases:
                place_had_cases = (
                    (new_case["last_available_confirmed"] or 0) != 0
                    or (new_case["last_available_deaths"] or 0) != 0
                )
                had_cases[place_key] = place_had_cases
            last_case_for_place[place_key] = new_case
            if place_had_cases:
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
