import csv

CITY_NAME_CSV_COLUMN = 0
CONFIRMED_CASES_CSV_COLUMN = 1
DEATH_CASES_CSV_COLUMN = 2


class MaranhaoCSVBulletinExtractor:
    def __init__(self, filename):
        self.filename = filename

    @property
    def data(self):
        with open(self.filename, encoding="mac_iceland") as fobj:
            reader = csv.reader(fobj, delimiter=";", lineterminator="\n")
            header = (
                None
            )  # There are blank lines in the begining of the file. Wait until find the header
            for line in reader:
                # Consider only non-empty lines and first 3 columns
                line = [cell.strip() for cell in line[:3]]
                if not any(line):
                    continue
                elif not header:
                    if line[CITY_NAME_CSV_COLUMN] == "MUNICÍPIOS":
                        header = line
                    continue
                yield {
                    "municipio": line[CITY_NAME_CSV_COLUMN],
                    "confirmados": line[CONFIRMED_CASES_CSV_COLUMN],
                    "mortes": line[DEATH_CASES_CSV_COLUMN],
                }
