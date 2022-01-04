from datetime import datetime, date
from typing import Optional
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


class RowsPtBrIntegerField(rows.fields.IntegerField):
    """IntegerField which removes `.` (thousands separator in Portuguese)"""

    @classmethod
    def deserialize(cls, value):
        return super().deserialize(value.replace(".", "").replace(",", "."))
