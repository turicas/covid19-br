import csv
from pathlib import Path

from covid19br.parsers.tocantins import TocantinsBulletinExtractor


def sorted_dicts(data):
    # Prepare dicts to be compared
    return sorted(sorted((key, str(value)) for key, value in obj.items()) for obj in data)


def run_parser_asserts(pdf_filename):
    expected_csv = pdf_filename.parent / pdf_filename.name.replace(".pdf", ".csv")
    try:
        parser = TocantinsBulletinExtractor(pdf_filename)
    except RuntimeError:  # Not a PDF
        assert not expected_csv.exists(), "File is not a PDF but a CSV was found"
    else:
        with open(expected_csv) as fobj:
            expected_data = list(csv.DictReader(fobj))
        data = list(parser.data)
        assert sorted_dicts(expected_data) == sorted_dicts(data)


def test_01():
    run_parser_asserts(Path("tests/data/TO-2021-08-01.pdf"))

def test_02():
    run_parser_asserts(Path("tests/data/TO-2022-01-22.pdf"))

def test_03():
    run_parser_asserts(Path("tests/data/TO-2022-02-02.pdf"))
