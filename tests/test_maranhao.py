from pathlib import Path

from covid19br.parsers.MA.maranhao_csv import MaranhaoCSVBulletinExtractor
from covid19br.parsers.MA.maranhao_pdf import MaranhaoPdfBulletinExtractor
from tests.test_utils import assert_data_equals_csv_content


def test_csv_report_with_latin_encoding():
    # given
    report_csv = Path("tests/data/MA/MA-report-2022-03-05.csv")
    # when
    parser = MaranhaoCSVBulletinExtractor(report_csv)
    # then
    expected_csv = Path("tests/data/MA/MA-2022-03-05.csv")
    assert_data_equals_csv_content(parser.data, expected_csv)


def test_csv_report_with_mac_iceland_encoding():
    # given
    report_csv = Path("tests/data/MA/MA-report-2022-03-06.csv")
    # when
    parser = MaranhaoCSVBulletinExtractor(report_csv)
    # then
    expected_csv = Path("tests/data/MA/MA-2022-03-06.csv")
    assert_data_equals_csv_content(parser.data, expected_csv)


def test_extract_total_from_pdf():
    # given
    report_pdf = Path("tests/data/MA/MA-2022-06-03.pdf")
    # when
    parser = MaranhaoPdfBulletinExtractor(report_pdf)
    # then
    assert parser.official_total == {"confirmados": "10832", "mortes": "415169"}
