import csv
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

from rows.utils import download_file, open_compressed


def download(date, cache=True):
    data_path = Path(__file__).parent / "data"
    if not data_path.exists():
        data_path.mkdir()
    url = f"https://data.brasil.io/dataset/covid19/backup/{date}/obito_cartorio.csv.gz"
    filename = data_path / f"{date}-obito_cartorio.csv.gz"
    if not cache or not filename.exists():
        download_file(url, filename, progress=True)
    return filename


def read_data(filename):
    fobj = open_compressed(filename)
    data = defaultdict(dict)
    for row in csv.DictReader(fobj):
        state, date = row.pop("state"), row.pop("date")
        row = {key: int(value) if value else None for key, value in row.items()}
        data[state][date] = row
    fobj.close()
    return data


def check_values(d1, d2):
    # TODO: implement many checks
    result = []
    for key, value in d1.items():
        if value > d2[key]:
            result.append(key)
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("date1", help="Data no formato YYYY-MM-DD")
    parser.add_argument("date2", help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()
    date1, date2 = args.date1, args.date2
    if date1 > date2:
        date1, date2 = date2, date1  # Python <3
    elif date1 == date2:
        print("ERRO: as datas precisam ser diferentes")
        exit(1)

    filename1 = download(date1)
    filename2 = download(date2)
    data1 = read_data(filename1)
    data2 = read_data(filename2)

    for state, state_data in data1.items():
        for date, values1 in state_data.items():
            values2 = data2[state].get(date)
            if values2 is None:
                continue
            keys = check_values(values1, values2)  # v1 must be <= v2
            if keys:
                print(state, date, {key: (values1[key], values2[key]) for key in keys})

    # TODO: implement a proper report
