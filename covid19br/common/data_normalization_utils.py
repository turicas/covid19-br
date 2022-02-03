from datetime import datetime, date
from typing import Optional
import unicodedata
import rows


class NormalizationUtils:
    @staticmethod
    def ensure_integer(value, allow_null: bool = True) -> Optional[int]:
        if value is None and allow_null:
            return value
        try:
            return int(value)
        except ValueError:
            return int(value.replace(".", "").replace(",", ""))

    @staticmethod
    def extract_datetime(value) -> datetime:
        return datetime.strptime(value, "%d/%m/%Y %H:%M")

    @staticmethod
    def extract_date(value) -> date:
        return datetime.strptime(value, "%d/%m/%Y").date()

    @staticmethod
    def remove_accentuation(original_text):
        return (
            unicodedata
            .normalize("NFKD", original_text)
            .encode("ascii", errors="ignore")
            .decode("ascii")
        )

    @staticmethod
    def month_name_to_number(month_name):
        month = month_name.lower()
        if month in ['janeiro', 'jan']:
            return 1
        if month in ['fevereiro', 'fev']:
            return 2
        if month in ['março', 'marco', 'mar']:
            return 3
        if month in ['abril', 'abr']:
            return 4
        if month in ['maio', 'mai']:
            return 5
        if month in ['junho', 'jun']:
            return 6
        if month in ['julho', 'jul']:
            return 7
        if month in ['agosto', 'ago']:
            return 8
        if month in ['setembro', 'set']:
            return 9
        if month in ['outubro', 'out']:
            return 10
        if month in ['novembro', 'nov']:
            return 11
        if month in ['dezembro', 'dez']:
            return 12
        raise ValueError(f'"{month_name}" is not a valid month name.')


class RowsPtBrIntegerField(rows.fields.IntegerField):
    """IntegerField which removes `.` (thousands separator in Portuguese)"""

    @classmethod
    def deserialize(cls, value):
        return super().deserialize(value.replace(".", "").replace(",", "."))
