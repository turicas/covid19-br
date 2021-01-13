from collections import defaultdict
from itertools import groupby

import rows

import demographics


def extract_boletim(state, data):
    table = rows.import_from_dicts(
        data,
        force_types={
            "date": rows.fields.DateField,
            "notes": rows.fields.TextField,
            "state": rows.fields.TextField,
            "url": rows.fields.TextField,
        },
    )
    for row in table:
        row = row._asdict()
        yield row


def extract_caso(state, data):
    cities = defaultdict(dict)
    for caso in data:
        for key, value in caso.items():
            if key == "municipio":
                city_info = demographics.get_city(state, value)
                if city_info:
                    caso["municipio"] = city_info.city
                continue
            elif key.startswith("confirmados_") or key.startswith("mortes_"):
                try:
                    _, day, month = key.split("_")
                except ValueError:
                    message = f"ERROR PARSING {repr(key)} - {repr(value)} - {caso}"
                    raise ValueError(message)
                # TODO: fix this
                if f"{int(month):02d}-{int(day):02d}" < "01-31":
                    year = 2021
                else:
                    year = 2020
                date = f"{year}-{int(month):02d}-{int(day):02d}"
                if key.startswith("confirmados_"):
                    number_type = "confirmed"
                elif key.startswith("mortes_"):
                    number_type = "deaths"
            else:
                continue
            if date not in cities[caso["municipio"]]:
                cities[caso["municipio"]][date] = {}
            if value in (None, ""):
                value = None
            else:
                value = str(value)
                if value.endswith(".0"):
                    value = value[:-2]
                if value.startswith("=") and value[1:].isdigit():
                    value = value[1:]
                try:
                    value = int(value)
                except ValueError:
                    message = f"ERROR converting to int: {date} {number_type} {value} {caso}"
                    raise ValueError(message)
            cities[caso["municipio"]][date][number_type] = value
    result = []
    for city, city_data in cities.items():
        for date, date_data in city_data.items():
            confirmed = date_data["confirmed"]
            deaths = date_data["deaths"]
            if confirmed is None and deaths is None:
                continue
            confirmed = int(confirmed) if confirmed is not None else None
            deaths = int(deaths) if deaths is not None else None
            row = {
                "date": date,
                "state": state,
                "city": city if city != "TOTAL NO ESTADO" else "",
                "place_type": "city" if city != "TOTAL NO ESTADO" else "state",
                "confirmed": confirmed,
                "deaths": deaths,
            }
            confirmed = row["confirmed"]
            deaths = row["deaths"]
            NULL = (None, "")
            if (confirmed in NULL and deaths not in NULL) or (deaths in NULL and confirmed not in NULL):
                message = f"ERROR: only one field is filled for {date}, {state}, {city}"
                raise ValueError(message)
            result.append(row)

    row_key = lambda row: (row["state"], row["city"], row["place_type"])
    result.sort(key=row_key)
    groups = groupby(result, key=row_key)
    for key, row_list_it in groups:
        row_list = list(row_list_it)
        row_list.sort(key=lambda row: row["date"])
        for order_for_place, row in enumerate(row_list, start=1):
            row["order_for_place"] = order_for_place
            row["is_last"] = False
        if row_list:
            row_list[-1]["is_last"] = True

    for row in result:
        if row["place_type"] == "city":
            if row["city"] == "Importados/Indefinidos":
                row_population_2020 = row_population_2019 = None
                row_city_code = None
            else:
                row_city_code = demographics.city_code(row["state"], row["city"])
                row_population_2019 = demographics.city_population(row["state"], row["city"], year=2019)
                row_population_2020 = demographics.city_population(row["state"], row["city"], year=2020)
        elif row["place_type"] == "state":
            row_city_code = demographics.state_code(row["state"])
            row_population_2019 = demographics.state_population(row["state"], year=2019)
            row_population_2020 = demographics.state_population(row["state"], year=2020)
        else:
            message = f"Invalid row: {row}"
            raise ValueError(message)
        row_deaths = row["deaths"]
        row_confirmed = row["confirmed"]
        confirmed_per_100k = (
            100_000 * (row_confirmed / row_population_2020) if row_confirmed and row_population_2020 else None
        )
        death_rate = row_deaths / row_confirmed if row_deaths is not None and row_confirmed not in (None, 0) else 0
        row["estimated_population_2019"] = row_population_2019
        row["estimated_population"] = row_population_2020
        row["city_ibge_code"] = row_city_code
        row["confirmed_per_100k_inhabitants"] = f"{confirmed_per_100k:.5f}" if confirmed_per_100k else None
        row["death_rate"] = f"{death_rate:.4f}"
        yield row
