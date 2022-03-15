import csv


def _sorted_dicts(data):
    # Prepare dicts to be compared
    return sorted(
        sorted((key, str(value)) for key, value in obj.items()) for obj in data
    )


def assert_data_equals_csv_content(data: list, expected_csv_filename: str):
    with open(expected_csv_filename) as fobj:
        expected_data = list(csv.DictReader(fobj))
    assert _sorted_dicts(expected_data) == _sorted_dicts(data)
