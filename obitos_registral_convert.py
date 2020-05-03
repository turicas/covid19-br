import argparse
import datetime
import json
from collections import Counter
from itertools import groupby

import rows
from tqdm import tqdm

from date_utils import brazilian_epidemiological_week, one_day

def convert_file(filename):
    table = rows.import_from_csv(filename)
    row_key = lambda row: (row.date, row.state)
    table = sorted(table, key=row_key)
    accumulated = Counter()
    for key, data in groupby(table, key=row_key):
        date, state = key
        row = {"date": date, "state": state}
        try:
            this_day_in_2019 = datetime.date(2019, date.month, date.day)
        except ValueError:  # This day does not exist in 2019 (29 February)
            yesterday = date - one_day
            this_day_in_2019 = datetime.date(2019, yesterday.month, yesterday.day)
        row["epidemiological_week_2019"] = brazilian_epidemiological_week(
            this_day_in_2019
        )[1]
        row["epidemiological_week_2020"] = brazilian_epidemiological_week(date)[1]

        for item in data:
            row["new_deaths_sars_2019"] = item.sars_2019
            row["new_deaths_pneumonia_2019"] = item.pneumonia_2019
            row["new_deaths_respiratory_failure_2019"] = item.respiratory_failure_2019
            row["new_deaths_septicemia_2019"] = item.septicemia_2019
            row["new_deaths_indeterminate_2019"] = item.indeterminate_2019
            row["new_deaths_others_2019"] = item.others_2019
            row["new_deaths_sars_2020"] = item.sars_2020
            row["new_deaths_pneumonia_2020"] = item.pneumonia_2020
            row["new_deaths_respiratory_failure_2020"] = item.respiratory_failure_2020
            row["new_deaths_septicemia_2020"] = item.septicemia_2020
            row["new_deaths_indeterminate_2020"] = item.indeterminate_2020
            row["new_deaths_others_2020"] = item.others_2020
            row["new_deaths_covid19"] = item.covid
        
        new_deaths_total = Counter()
        for year in ("2019", "2020"):
            for cause in (
                "sars",
                "pneumonia",
                "respiratory_failure",
                "septicemia",
                "indeterminate",
                "others"
            ):
                accumulated_key = f"{state}-{cause}-{year}"
                new_deaths = row[f"new_deaths_{cause}_{year}"]
                accumulated[accumulated_key] += new_deaths
                row[f"deaths_{cause}_{year}"] = accumulated[accumulated_key]
                new_deaths_total[f"{year}"] += new_deaths

        accumulated[f"{state}-covid19"] += row["new_deaths_covid19"]
        row["deaths_covid19"] = accumulated[f"{state}-covid19"]
        new_deaths_total["2020"] += row["new_deaths_covid19"]

        row["new_deaths_total_2019"] = new_deaths_total["2019"]
        row["new_deaths_total_2020"] = new_deaths_total["2020"]

        accumulated[f"{state}-total-2019"] += row["new_deaths_total_2019"]
        accumulated[f"{state}-total-2020"] += row["new_deaths_total_2020"]

        row["deaths_total_2019"] = accumulated[f"{state}-total-2019"]
        row["deaths_total_2020"] = accumulated[f"{state}-total-2020"]
        yield row

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in tqdm(convert_file(args.input_filename)):
        writer.writerow(row)
