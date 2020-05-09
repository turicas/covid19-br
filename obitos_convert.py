import argparse
import datetime
from collections import Counter
from itertools import groupby

import rows
from tqdm import tqdm

from date_utils import brazilian_epidemiological_week, one_day

from obitos_spider import DeathsSpider
DEATH_CAUSES = list(DeathsSpider.causes_map.keys())
ALL_YEARS = ["2019", "2020"]

def get_death_cause_key(prefix, cause, year):
    if cause == "covid19":
        return f"{prefix}_{cause}" if year == "2020" else None

    return f"{prefix}_{cause}_{year}" 

def iterate_year_causes_keys(prefix, years):
    for year in years:
        for cause in DEATH_CAUSES:
            key = get_death_cause_key(prefix, cause, year)
            if key: 
                yield (year, cause, key)

def convert_file(filename):
    table = rows.import_from_csv(filename)
    row_key = lambda row: (row.state, datetime.date(2020, row.date.month, row.date.day))
    table = sorted(table, key=row_key)
    accumulated = Counter()
    for key, data in groupby(table, key=row_key):
        state, date = key
        row = { "date": date, "state": state }

        try:
            this_day_in_2019 = datetime.date(2019, date.month, date.day)
        except ValueError:  # This day does not exist in 2019 (29 February)
            yesterday = date - one_day
            this_day_in_2019 = datetime.date(2019, yesterday.month, yesterday.day)
        row["epidemiological_week_2019"] = brazilian_epidemiological_week(
            this_day_in_2019
        )[1]
        row["epidemiological_week_2020"] = brazilian_epidemiological_week(date)[1]

        # There are some missing data on the registral, so default all to None
        # Multiple passes to keep the same column ordering
        for year, cause, key in iterate_year_causes_keys("new_deaths", ALL_YEARS):
            row[key] = None
        for year, cause, key in iterate_year_causes_keys("deaths", ALL_YEARS):
            row[key] = None
        for year in ALL_YEARS:
            row[f"new_deaths_total_{year}"] = None
        for year in ALL_YEARS:
            row[f"deaths_total_{year}"] = None

        for item in data:
            for year, cause, key in iterate_year_causes_keys("new_deaths", [str(item.date.year)]):
                row[key] = getattr(item, cause)

        new_deaths_total = Counter()
        for year, cause, key in iterate_year_causes_keys("new_deaths", ALL_YEARS):
            new_deaths = row[key]
            if new_deaths:
                accumulated_key = f"{state}-{cause}-{year}"
                accumulated[accumulated_key] += new_deaths
                row[get_death_cause_key("deaths", cause, year)] = accumulated[accumulated_key]
                new_deaths_total[f"{year}"] += new_deaths

        for year in ALL_YEARS:
            accumulated[f"{state}-total-{year}"] += new_deaths_total[year]
            row[f"new_deaths_total_{year}"] = new_deaths_total[year]
            row[f"deaths_total_{year}"] = accumulated[f"{state}-total-{year}"]

        yield row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in tqdm(convert_file(args.input_filename)):
        writer.writerow(row)
