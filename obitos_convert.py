import argparse
from itertools import groupby

import rows
from tqdm import tqdm

from date_utils import brazilian_epidemiological_week


def convert_file(filename):
    table = rows.import_from_csv(filename)
    row_key = lambda row: (row.date, row.state)
    table = sorted(table, key=row_key)
    for key, data in groupby(table, key=row_key):
        date, state = key
        row = {"date": date, "state": state}
        for item in data:
            assert item.data_type == "data_ocorrido"
            if item.search == "death-covid":
                row["deaths_covid19"] = item.qtd_2020
            elif item.search == "death-respiratory":
                if item.causa == "insuficiencia_respiratoria":
                    row["deaths_respiratory_failure_2019"] = item.qtd_2019
                    row["deaths_respiratory_failure_2020"] = item.qtd_2020
                elif item.causa == "pneumonia":
                    row["deaths_pneumonia_2019"] = item.qtd_2019
                    row["deaths_pneumonia_2020"] = item.qtd_2020
                else:
                    raise ValueError(f"Invalid value for cause: {item.causa}")
            else:
                raise ValueError(f"Invalid value for search: {item.search}")
        row["epidemiological_week_2019"] = brazilian_epidemiological_week(2019, datetime.date(2019, date.month, date.day))
        row["epidemiological_week_2020"] = brazilian_epidemiological_week(2020, date)
        yield row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in tqdm(convert_file(args.input_filename)):
        writer.writerow(row)
