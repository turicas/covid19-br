import csv
from itertools import groupby
from pathlib import Path

from rows.utils import CsvLazyDictWriter
from tqdm import tqdm


def merge_files(filenames, output_filename):
    groups = groupby(
        filenames, key=lambda row: row.name.split("T")[0].replace("ocupacao-", "")
    )
    progress = tqdm()
    writer = CsvLazyDictWriter(output_filename)
    for index, (date, group) in enumerate(groups, start=1):
        progress.desc = f"Processing file {index}"
        group = sorted(group)
        filename = group[-1]  # Process only the last file per day
        dt = filename.name.split("ocupacao-")[1].split(".csv")[0]
        base_row = {"datahora": dt}
        with open(filename) as fobj:
            reader = csv.DictReader(fobj)
            for row in reader:
                new = base_row.copy()
                new.update({key.lower(): value for key, value in row.items()})
                writer.writerow(new)
                progress.update()
    progress.close()
    writer.close()


if __name__ == "__main__":
    DOWNLOAD_PATH = Path("data/ocupacao")

    merge_files(
        filenames=sorted(DOWNLOAD_PATH.glob("ocupacao-*.csv")),
        output_filename=DOWNLOAD_PATH / "ocupacao.csv.gz",
    )
