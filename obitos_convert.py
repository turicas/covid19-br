import argparse
import datetime
from collections import Counter
from functools import lru_cache
from itertools import chain, groupby

import rows
from tqdm import tqdm

from date_utils import brazilian_epidemiological_week, one_day
from obitos_spider import DeathsSpider

RESPIRATORY_DEATH_CAUSES = list(DeathsSpider.causes_map["respiratory"].values())
YEAR_CHOICES = (2019, 2020)
PREFIX_CHOICES = ("deaths", "new_deaths")


@lru_cache
def get_death_cause_key(prefix, cause, year):
    if prefix not in PREFIX_CHOICES:
        raise ValueError(f"Unknown prefix {repr(prefix)}")
    elif cause not in RESPIRATORY_DEATH_CAUSES + ["total"]:
        raise ValueError(f"Unknown cause {repr(cause)}")
    elif year not in YEAR_CHOICES:
        raise ValueError(f"Unknown year {repr(year)}")

    if cause == "covid19":
        return f"{prefix}_{cause}" if year == 2020 else None

    return f"{prefix}_{cause}_{year}"


@lru_cache
def year_causes_keys(prefix, years):
    result = []
    for year in years:
        for cause in RESPIRATORY_DEATH_CAUSES:
            key = get_death_cause_key(prefix, cause, year)
            if key is not None:
                result.append(key)
    return result


def convert_file(filename):
    # There are some missing data on the registral, so default all to None
    # Multiple passes to keep the same column ordering
    all_keys = chain(
        year_causes_keys("new_deaths", YEAR_CHOICES),
        year_causes_keys("deaths", YEAR_CHOICES),
        [f"new_deaths_total_{year}" for year in YEAR_CHOICES],
        [f"deaths_total_{year}" for year in YEAR_CHOICES],
    )
    base_row = {}
    for key in all_keys:
        base_row[key] = None

    table_types = {
        "date": rows.fields.DateField,
        "state": rows.fields.TextField,
        "cause": rows.fields.TextField,
        "total": rows.fields.IntegerField,
    }
    table = rows.import_from_csv(filename, force_types=table_types)
    row_key = lambda row: (row.state, datetime.date(2020, row.date.month, row.date.day))
    table = sorted(table, key=row_key)
    accumulated = Counter()
    for key, state_data in groupby(table, key=row_key):
        state, date = key
        row = {
            "date": date,
            "state": state,
        }
        try:
            this_day_in_2019 = datetime.date(2019, date.month, date.day)
        except ValueError:  # This day does not exist in 2019 (29 February)
            yesterday = date - one_day
            this_day_in_2019 = datetime.date(2019, yesterday.month, yesterday.day)
        row["epidemiological_week_2019"] = brazilian_epidemiological_week(
            this_day_in_2019
        )[1]
        row["epidemiological_week_2020"] = brazilian_epidemiological_week(date)[1]
        row.update(base_row)

        # Zero sum of new deaths for this state in all years (will accumulate)
        for year in YEAR_CHOICES:
            accumulated[(year, state, "new-total")] = 0

        # For each death cause in this date/state, fill `row` and accumulate
        for item in state_data:
            cause = item.cause
            year = item.date.year
            key = get_death_cause_key("new_deaths", cause, year)
            new_deaths = item.total
            if key is None:
                if new_deaths > 0:
                    raise RuntimeError(f"Cannot have new_deaths > 0 when key for (new_deaths, {cause}, {year}) is None")
                else:
                    continue
            row[key] = new_deaths
            accumulated_key = (year, state, cause)
            accumulated_key_total = (year, state, "total")
            accumulated_key_new_total = (year, state, "new-total")
            accumulated[accumulated_key] += new_deaths
            accumulated[accumulated_key_total] += new_deaths
            accumulated[accumulated_key_new_total] += new_deaths
            row[get_death_cause_key("deaths", cause, year)] = accumulated[accumulated_key]

        for year in YEAR_CHOICES:
            row[get_death_cause_key("new_deaths", "total", year)] = accumulated[(year, state, "new-total")]
            row[get_death_cause_key("deaths", "total", year)] = accumulated[(year, state, "total")]

        yield row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in tqdm(convert_file(args.input_filename)):
        writer.writerow(row)
