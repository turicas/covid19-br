import argparse
import datetime
from collections import Counter
from functools import lru_cache
from itertools import groupby

import rows
from rows.utils.date import today
from tqdm import tqdm

from covid19br.utils import brazilian_epidemiological_week, one_day
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
    all_keys = []
    for prefix in PREFIX_CHOICES:
        all_keys.extend(year_causes_keys(prefix, YEAR_CHOICES))
        all_keys.extend([f"{prefix}_total_{year}" for year in YEAR_CHOICES])
    base_row = {}
    for key in all_keys:
        base_row[key] = 0 if key.startswith("deaths_") else None

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
    last_day = today()
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
        row["epidemiological_week_2019"] = brazilian_epidemiological_week(this_day_in_2019)[1]
        row["epidemiological_week_2020"] = brazilian_epidemiological_week(date)[1]
        row.update(base_row)

        # Zero sum of new deaths for this state in all years (will accumulate)
        for year in YEAR_CHOICES:
            accumulated[(year, state, "new-total")] = 0

        # For each death cause in this date/state, fill `row` and accumulate
        filled_causes = set()
        for item in state_data:
            cause = item.cause
            year = item.date.year
            key_new = get_death_cause_key("new_deaths", cause, year)
            new_deaths = item.total
            if key_new is None:
                if new_deaths > 0:
                    # raise RuntimeError(f"Cannot have new_deaths > 0 when key for (new_deaths, {cause}, {year}) is None")
                    print(f"ERROR converting {item}: new_deaths > 0 but key is None")
                    continue
                else:
                    continue
            accumulated_key = (year, state, cause)
            accumulated_key_total = (year, state, "total")
            accumulated_key_new_total = (year, state, "new-total")
            accumulated[accumulated_key] += new_deaths
            accumulated[accumulated_key_total] += new_deaths
            accumulated[accumulated_key_new_total] += new_deaths
            row[key_new] = new_deaths
            row[get_death_cause_key("deaths", cause, year)] = accumulated[accumulated_key]
            filled_causes.add((year, cause))

        # Fill other deaths_* (accumulated) values with the last available data
        # if not filled by the state_data for this date.
        for cause in RESPIRATORY_DEATH_CAUSES:
            for year in YEAR_CHOICES:
                if (year, cause) in filled_causes:
                    continue
                accumulated_key = (year, state, cause)
                key_name = get_death_cause_key("deaths", cause, year)
                if key_name is None:
                    continue
                row[key_name] = accumulated[accumulated_key]

        # Fill year totals (new and accumulated) for state
        for year in YEAR_CHOICES:
            if year == last_day.year and date > last_day:
                new_total = None
            else:
                new_total = accumulated[(year, state, "new-total")]
            total = accumulated[(year, state, "total")]
            row[get_death_cause_key("new_deaths", "total", year)] = new_total
            row[get_death_cause_key("deaths", "total", year)] = total

        yield row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in tqdm(convert_file(args.input_filename)):
        writer.writerow(row)
