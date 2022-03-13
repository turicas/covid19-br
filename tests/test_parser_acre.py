import csv
from pathlib import Path

from covid19br.parsers.acre import AcreBulletinExtractor


def sorted_dicts(data):
    # Prepare dicts to be compared
    return sorted(sorted((key, str(value)) for key, value in obj.items()) for obj in data)


def run_parser_asserts(pdf_filename, expected_official_total):
    parser = AcreBulletinExtractor(pdf_filename)

    assert parser.official_total == expected_official_total

    expected_csv = pdf_filename.parent / pdf_filename.name.replace(".pdf", ".csv")
    with open(expected_csv) as fobj:
        expected_data = list(csv.DictReader(fobj))
    data = list(parser.data)
    assert sorted_dicts(expected_data) == sorted_dicts(data)


def test_01_pdf_with_ghost_objs_in_first_page():
    parser = AcreBulletinExtractor(Path("tests/data/AC/TO-2022-01-30.pdf"))
    assert parser.official_total == {"confirmados": "98.149", "mortes": "1.868"}
    assert not list(parser.data)


def test_02_pdf_without_cities_table():
    parser = AcreBulletinExtractor(Path("tests/data/AC/TO-2022-02-12.pdf"))
    assert parser.official_total == {"confirmados": "110.430", "mortes": "1.917"}
    assert not list(parser.data)


def test_03_pdf_with_cities_table():
    run_parser_asserts(Path("tests/data/AC/TO-2022-02-25.pdf"), {"confirmados": "120.569", "mortes": "1.969"})
