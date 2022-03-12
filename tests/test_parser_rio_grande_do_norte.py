import csv
from pathlib import Path

import sys
sys.path.append("/Users/appsimples/MyProjects/covid19-br")


from covid19br.parsers.rio_grande_do_norte import RioGrandeDoNorteBulletinExtractor


def sorted_dicts(data):
    # Prepare dicts to be compared
    return sorted(sorted((key, str(value)) for key, value in obj.items()) for obj in data)


def run_parser_asserts(pdf_filename):
    expected_csv = pdf_filename.parent / pdf_filename.name.replace(".pdf", ".csv")
    try:
        parser = RioGrandeDoNorteBulletinExtractor(pdf_filename)
    except RuntimeError:  # Not a PDF
        assert not expected_csv.exists(), "File is not a PDF but a CSV was found"
    else:
        with open(expected_csv) as fobj:
            expected_data = list(csv.DictReader(fobj))
        data = list(parser.data)
        assert sorted_dicts(expected_data) == sorted_dicts(data)


def test_01():
    run_parser_asserts(Path("tests/data/RN/RN-2022-03-11.pdf"))
