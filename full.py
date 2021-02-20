import argparse
import datetime
from collections import Counter, defaultdict
from functools import lru_cache
from multiprocessing import cpu_count
from operator import attrgetter
from pathlib import Path

import rows
from async_process_executor import AsyncProcessExecutor, Task
from rows.utils import load_schema
from rows.utils.date import date_range, today
from tqdm import tqdm

from covid19br import demographics

DATA_PATH = Path(__file__).parent / "data"
SCHEMA_PATH = Path(__file__).parent / "schema"


def read_cases(input_filename, order_by=None):
    cases = rows.import_from_csv(input_filename, force_types=load_schema(str(SCHEMA_PATH / "caso.csv")))
    if order_by:
        cases.order_by(order_by)
    return cases


@lru_cache()
def read_epidemiological_week():
    # TODO: use pkg_resources to get correct path
    filename = "covid19br/data/epidemiological-week.csv"
    table = rows.import_from_csv(filename)
    return {row.date: int(f"{row.epidemiological_year}{row.epidemiological_week:02d}") for row in table}


@lru_cache(maxsize=6000)
def epidemiological_week(date):
    return read_epidemiological_week()[date]


def row_key(row):
    return (row.place_type, row.state, row.city or None)


def get_data(input_filename, start_date=None, end_date=None):
    casos = read_cases(input_filename, order_by="date")
    dates = sorted(set(c.date for c in casos))
    start_date = start_date or dates[0]
    end_date = end_date or dates[-1]
    caso_by_key = defaultdict(list)
    for caso in casos:
        caso_by_key[row_key(caso)].append(caso)
    for place_cases in caso_by_key.values():
        place_cases.sort(key=lambda row: row.date, reverse=True)

    order_key = attrgetter("order_for_place")
    last_case_for_place = {}
    order_for_place = Counter()
    for date in date_range(start_date, end_date + datetime.timedelta(days=1), "daily"):
        for place_key in demographics.place_keys():
            place_type, state, city = place_key
            place_cases = caso_by_key[place_key]
            valid_place_cases = sorted(
                [item for item in place_cases if item.date <= date], key=order_key, reverse=True,
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
                "estimated_population": last_valid_case.estimated_population,
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
                new_confirmed = new_case["last_available_confirmed"] - last_case["last_available_confirmed"]
                new_deaths = new_case["last_available_deaths"] - last_case["last_available_deaths"]
            new_case["new_confirmed"] = new_confirmed
            new_case["new_deaths"] = new_deaths
            last_case_for_place[place_key] = new_case

            yield new_case


def get_data_greedy(input_filename, start_date=None, end_date=None):
    return list(get_data(input_filename, start_date=start_date, end_date=end_date))


class CasoFullTaskExecutor(AsyncProcessExecutor):
    def __init__(self, input_filenames, output_filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_filenames = input_filenames
        self.writer = rows.utils.CsvLazyDictWriter(output_filename)
        self.progress = tqdm()

    async def tasks(self):
        start_date = None
        end_date = today()
        for filename in self.input_filenames:
            yield Task(function=get_data_greedy, args=(filename, start_date, end_date))

    async def process(self, result):
        write_row = self.writer.writerow
        progress_update = self.progress.update
        for row in result:
            write_row(row)
            progress_update()

    async def finished(self, task):
        self.writer.close()
        self.progress.close()


def main():
    workers = cpu_count() - 1
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filenames", nargs="+")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    CasoFullTaskExecutor(
        input_filenames=args.input_filenames, output_filename=args.output_filename, workers=workers,
    ).run()


if __name__ == "__main__":
    main()
