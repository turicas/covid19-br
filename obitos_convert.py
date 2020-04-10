import argparse
import datetime
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
        for item in data:
            assert item.data_type == "data_ocorrido"
            if item.search == "death-covid":
                row["new_deaths_covid19"] = item.qtd_2020
            elif item.search == "death-respiratory":
                if item.causa == "insuficiencia_respiratoria":
                    row["new_deaths_respiratory_failure_2019"] = item.qtd_2019
                    row["new_deaths_respiratory_failure_2020"] = item.qtd_2020
                elif item.causa == "pneumonia":
                    row["new_deaths_pneumonia_2019"] = item.qtd_2019
                    row["new_deaths_pneumonia_2020"] = item.qtd_2020
                else:
                    raise ValueError(f"Invalid value for cause: {item.causa}")
            else:
                raise ValueError(f"Invalid value for search: {item.search}")

        try:
            this_day_in_2019 = datetime.date(2019, date.month, date.day)
        except ValueError:  # This day does not exist in 2019 (29 Februrary)
            yesterday = date - one_day
            this_day_in_2019 = datetime.date(2019, yesterday.month, yesterday.day)
        row["epidemiological_week_2019"] = brazilian_epidemiological_week(
            this_day_in_2019
        )[1]
        row["epidemiological_week_2020"] = brazilian_epidemiological_week(date)[1]
        for key in (
            "deaths_covid19",
            "deaths_respiratory_failure_2019",
            "deaths_respiratory_failure_2020",
            "deaths_pneumonia_2019",
            "deaths_pneumonia_2020"
        ):
            counter_key = f"{state}-{key}"
            accumulated[counter_key] += row[f"new_{key}"]
            row[key] = accumulated[counter_key]
        yield row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in tqdm(convert_file(args.input_filename)):
        writer.writerow(row)
