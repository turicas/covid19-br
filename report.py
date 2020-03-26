import argparse
import csv
import gzip
import io
import json
from itertools import groupby
from pathlib import Path
from urllib.request import urlopen

from rows.fields import make_header
from rows.utils import load_schema

BASE_DIR = Path(__file__).parent


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


def get_brasilio_data(dataset, table, limit=None):
    url = f"https://brasil.io/api/dataset/{dataset}/{table}/data"
    if limit:
        url += f"?page_size={limit}"

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=["api", "local"])
    args = parser.parse_args()

    if args.source == "api":
        boletins = get_brasilio_data("covid19", "boletim")
        casos = get_brasilio_data("covid19", "caso")
    elif args.source == "local":
        boletins = get_local_data("boletim")
        casos = get_local_data("caso")

    state_rows = list(filter_rows(casos, is_last=True, place_type="state"))
    city_rows = list(filter_rows(casos, is_last=True, place_type="city"))

    confirmados_estados = sum(row["confirmed"] for row in state_rows)
    confirmados_municipios = sum(row["confirmed"] for row in city_rows)
    mortes_estados = sum(row["deaths"] for row in state_rows)
    mortes_municipios = sum(row["deaths"] for row in city_rows)
    print(f"*DADOS ATUALIZADOS*")
    print(f"- {len(boletins)} boletins capturados")
    print(f"- {confirmados_estados} casos confirmados (estado)")
    print(f"- {confirmados_municipios} casos confirmados (municípios)")
    print(f"- {mortes_estados} mortes (estado)")
    print(f"- {mortes_municipios} mortes (municípios)")

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
            confirmed_state = sum(row["confirmed"] for row in state_rows)
            deaths_state = sum(row["deaths"] for row in state_rows)

        confirmed_cities = sum(row["confirmed"] for row in city_rows)
        deaths_cities = sum(row["deaths"] for row in city_rows)

        if confirmed_state != confirmed_cities:
            confirmed_diff.append(f"{state} ({confirmed_cities}/{confirmed_state})")
        if deaths_state != deaths_cities:
            deaths_diff.append(f"{state} ({deaths_cities}/{deaths_state})")
        if state_date != last_date:
            updated_diff.append(f"{state} ({state_date})")
    print()

    updated_diff = "- " + "\n- ".join(updated_diff)
    print(f"*DESATUALIZADOS*:")
    print(updated_diff)
    print()

    confirmed_diff = "- " + "\n- ".join(confirmed_diff)
    print(f"*CONFIRMADOS INCONSISTENTES*:")
    print(confirmed_diff)
    print()

    deaths_diff = "- " + "\n- ".join(deaths_diff)
    print(f"*MORTES INCONSISTENTES*:")
    print(deaths_diff)
    print()


if __name__ == "__main__":
    main()
