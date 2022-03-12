import csv
from pathlib import Path

from covid19br.parsers.rondonia import RondoniaBulletinExtractor


def sorted_dicts(data):
    # Prepare dicts to be compared
    return sorted(sorted((key, str(value)) for key, value in obj.items()) for obj in data)


def run_parser_asserts(pdf_filename):
    expected_csv = pdf_filename.parent / pdf_filename.name.replace(".pdf", ".csv")
    try:
        parser = RondoniaBulletinExtractor(pdf_filename)
    except RuntimeError:  # Not a PDF
        assert not expected_csv.exists(), "File is not a PDF but a CSV was found"
    else:
        with open(expected_csv) as fobj:
            expected_data = list(csv.DictReader(fobj))
        data = list(parser.data)
        assert sorted_dicts(expected_data) == sorted_dicts(data)


def test_01():
    run_parser_asserts(Path("tests/data/RO-2021-04-15.pdf"))

def test_02():
    run_parser_asserts(Path("tests/data/RO-2021-05-02.pdf"))

def test_03():
    run_parser_asserts(Path("tests/data/RO-2021-05-12.pdf"))

def test_04():
    run_parser_asserts(Path("tests/data/RO-2021-05-16.pdf"))

def test_05():
    run_parser_asserts(Path("tests/data/RO-2021-05-17.pdf"))

def test_06():
    run_parser_asserts(Path("tests/data/RO-2021-06-18.pdf"))

def test_07():
    run_parser_asserts(Path("tests/data/RO-2021-08-05.pdf"))

def test_08():
    run_parser_asserts(Path("tests/data/RO-2021-08-22.pdf"))

def test_09():
    run_parser_asserts(Path("tests/data/RO-2021-12-23.pdf"))

def test_10():
    run_parser_asserts(Path("tests/data/RO-2021-12-24.pdf"))

def test_11():
    run_parser_asserts(Path("tests/data/RO-2022-01-13.pdf"))

def test_12():
    run_parser_asserts(Path("tests/data/RO-2022-02-13.pdf"))

def test_13():
    run_parser_asserts(Path("tests/data/RO-2022-02-16.pdf"))

def test_14():
    run_parser_asserts(Path("tests/data/RO-2022-03-01.pdf"))
