import csv

CITY_NAME_CSV_COLUMN = 0
CONFIRMED_CASES_CSV_COLUMN = 1
DEATH_CASES_CSV_COLUMN = 2


class MaranhaoCSVBulletinExtractor:
    def __init__(self, filename):
        with open(filename, encoding="latin-1") as fobj:
            reader = csv.reader(fobj, delimiter=";", lineterminator="\n")
            self.file_content = list(reader)

        # We actually just need the header, but we are not sure about
        # it's position so we take the first 10 lines
        first_items = [l[0].strip() for l in self.file_content[:10]]
        # If the encoding is wrong, we try another one
        if "MUNICÍPIOS" not in first_items:
            with open(filename, encoding="mac_iceland") as fobj:
                reader = csv.reader(fobj, delimiter=";", lineterminator="\n")
                self.file_content = list(reader)

    @property
    def data(self):
        # There are blank lines in the beginning of the file. Wait until find the header
        header = None
        for line in self.file_content:
            # Consider only non-empty lines and first 3 columns
            line = [cell.strip() for cell in line[:3]]
            if not any(line):
                continue
            elif not header:
                if line[CITY_NAME_CSV_COLUMN] == "MUNICÍPIOS":
                    header = line
                continue

            if line[
                CITY_NAME_CSV_COLUMN
            ]:  # There are some blank lines we want to ignore
                yield {
                    "municipio": line[CITY_NAME_CSV_COLUMN],
                    "confirmados": line[CONFIRMED_CASES_CSV_COLUMN],
                    "mortes": line[DEATH_CASES_CSV_COLUMN],
                }
