import argparse
import datetime
import csv
import gzip
import io
import json
from collections import Counter
from itertools import groupby
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from rows.fields import make_header
from rows.utils import load_schema

BASE_DIR = Path(__file__).parent


def sum_all(data, key):
    return sum(row[key] for row in data if row[key] is not None)


class Schema:  # TODO: add this class to rows
    @classmethod
    def from_file(cls, filename):
        obj = cls()
        obj.filename = filename
        obj.fields = load_schema(
            str(filename)
        )  # TODO: load_schema must support Path objects
        return obj

    def deserialize(self, row):
        field_names = list(row.keys())
        field_mapping = {
            old: self.fields[new]
            for old, new in zip(field_names, make_header(field_names))
        }
        return {
            key: field_mapping[key].deserialize(value) for key, value in row.items()
        }


def get_brasilio_data(dataset, table, **filters):
    url = f"https://brasil.io/api/dataset/{dataset}/{table}/data"
    if filters:
        url += "?" + urlencode(filters)

    finished = False
    data = []
    while not finished:
        response = urlopen(url)
        response_data = json.loads(response.read())
        data.extend(response_data["results"])
        url = response_data["next"]
        if not url:
            finished = True
    return data


def get_local_data(table):
    schema = Schema.from_file(BASE_DIR / "schema" / f"{table}.csv")
    filename = BASE_DIR / "data" / "output" / f"{table}.csv.gz"
    with io.TextIOWrapper(gzip.GzipFile(filename), encoding="utf-8") as fobj:
        return [schema.deserialize(row) for row in csv.DictReader(fobj)]


def filter_rows(data, **kwargs):
    for row in data:
        if all(row[key] == value for key, value in kwargs.items()):
            yield row


def print_stats(title, data):
    print(f"*{title.upper()}*:")
    if not data:
        print("Nenhum! o/")
    else:
        data = "- " + "\n- ".join(data)
        print(data)
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=["api", "local"])
    args = parser.parse_args()

    if args.source == "api":
        boletins = get_brasilio_data("covid19", "boletim", is_last=True)
        casos = get_brasilio_data("covid19", "caso", is_last=True)
    elif args.source == "local":
        boletins = get_local_data("boletim")
        casos = get_local_data("caso")

    state_rows = list(filter_rows(casos, is_last=True, place_type="state"))
    city_rows = list(filter_rows(casos, is_last=True, place_type="city"))

    confirmados_estados = sum_all(state_rows, "confirmed")
    confirmados_municipios = sum_all(city_rows, "confirmed")
    mortes_estados = sum_all(state_rows, "deaths")
    mortes_municipios = sum_all(city_rows, "deaths")
    print_stats(
        "últimos dados",
        [
            f"{len(boletins)} boletins capturados",
            f"{confirmados_estados} casos confirmados (estado)",
            f"{confirmados_municipios} casos confirmados (municípios)",
            f"{mortes_estados} mortes (estado)",
            f"{mortes_municipios} mortes (municípios)",
        ],
    )

    casos.sort(key=lambda row: row["date"], reverse=True)
    last_date = casos[0]["date"]
    casos.sort(key=lambda row: row["state"])
    confirmed_diff, deaths_diff, updated_diff = [], [], []
    for state, data in groupby(casos, key=lambda row: row["state"]):
        data = list(data)
        state_date = max(row["date"] for row in data)
        state_rows = list(filter_rows(data, is_last=True, place_type="state"))
        city_rows = list(filter_rows(data, is_last=True, place_type="city"))
        if not state_rows:
            confirmed_state = None
            deaths_state = None
        else:
            confirmed_state = sum_all(state_rows, "confirmed")
            deaths_state = sum_all(state_rows, "deaths")
            state_date = state_rows[0]["date"]

        confirmed_cities = sum_all(city_rows, "confirmed")
        deaths_cities = sum_all(city_rows, "deaths")

        confirmed_differs = confirmed_state != confirmed_cities
        deaths_differs = deaths_state != deaths_cities
        date_count = Counter(row["date"] for row in city_rows)
        if len(date_count) > 1:
            wrong_cities = []
            for date, _ in date_count.most_common():
                if date != state_date:
                    wrong_cities.extend(list(filter_rows(city_rows, date=date)))
            wrong_str = " - municípios: " + ", ".join(
                sorted(
                    f"{row['city']} ({row['date']})"
                    for row in wrong_cities
                )
            )
        else:
            wrong_str = ""
        if confirmed_differs:
            confirmed_diff.append(
                f"{state} ({confirmed_cities}/{confirmed_state}){wrong_str}"
            )
        elif wrong_str:
            confirmed_diff.append(
                f"{state} {wrong_str}"
            )
        if deaths_differs:
            deaths_diff.append(
                f"{state} ({deaths_cities}/{deaths_state})"
            )
        if state_date != last_date:
            dias = abs(
                datetime.date.fromisoformat(str(state_date))
                - datetime.date.fromisoformat(str(last_date))
            ).days
            msg_atraso = f" - *{dias} dias de atraso*" if dias >= 2 else ""
            updated_diff.append(f"{state} ({state_date}){msg_atraso}")
    print_stats("desatualizados", updated_diff)
    print_stats("confirmados inconsistentes", confirmed_diff)
    print_stats("mortes inconsistentes", deaths_diff)


if __name__ == "__main__":
    main()
