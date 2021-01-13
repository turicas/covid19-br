import datetime
import json
from pathlib import Path

import converters

DATA_PATH = Path(__file__).absolute().parent / "data"


def date_to_json(obj):
    if not isinstance(obj, (datetime.date, datetime.datetime)):
        raise TypeError()
    return obj.isoformat()


def get_sample_data():
    with open(DATA_PATH / "AC.json") as fobj:
        return json.load(fobj)


def test_expected_boletim():
    state_data = get_sample_data()
    converted = list(converters.extract_boletim("AC", state_data["reports"]))
    # Convert back and forth JSON so it parses date/datetime correctly
    converted = json.loads(json.dumps(converted, default=date_to_json))

    with open(DATA_PATH / "AC-reports.json") as fobj:
        expected = json.load(fobj)

    assert expected == converted


def test_expected_caso():
    state_data = get_sample_data()
    converted = list(converters.extract_caso("AC", state_data["cases"]))
    # Convert back and forth JSON so it parses date/datetime correctly
    converted = json.loads(json.dumps(converted, default=date_to_json))

    with open(DATA_PATH / "AC-cases.json") as fobj:
        expected = json.load(fobj)

    assert expected == converted
