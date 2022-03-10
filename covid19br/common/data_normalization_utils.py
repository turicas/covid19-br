import unicodedata
import re
from datetime import date, datetime
from typing import Optional

import rows

CURRENT_YEAR = date.today().year
MONTHS = "jan fev mar abr mai jun jul ago set out nov dez".split()

REGEXP_IN_FULL_DATE = re.compile("([0-9]{1,2})(?: +de)? ([^ ]+)(?: de)?(?: ([0-9]{4}))?")
REGEXP_NUMERIC_DATE = re.compile("([0-9]{2})[/-]([0-9]{2})[/-]([0-9]{2,4})[ .]?")


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
    def str_to_datetime(value, separator=None) -> datetime:
        date_format = NormalizationUtils.detect_date_format(value, separator)
        return datetime.strptime(value, f"{date_format} %H:%M")

    @staticmethod
    def str_to_date(value, separator=None) -> date:
        date_format = NormalizationUtils.detect_date_format(value, separator)
        return datetime.strptime(value, date_format).date()

    @staticmethod
    def detect_date_format(value, sep) -> str:
        """
        >>> NormalizationUtils.detect_date_format("10/02/2034")
        "%d/%m/%Y"
        >>> NormalizationUtils.detect_date_format("18-09-2021")
        "%d-%m-%Y"
        >>> NormalizationUtils.detect_date_format("2021/07/09")
        "%Y/%m/%d"
        >>> NormalizationUtils.detect_date_format("2023-12-30")
        "%Y-%m-%d"
        >>> NormalizationUtils.detect_date_format("2023.12.30", sep=".")
        "%Y.%m.%d"
        """
        if not sep:
            sep = "/" if "/" in value else "-"
        first_number, *_ = value.split(sep)
        if len(first_number) == 2:
            return f"%d{sep}%m{sep}%Y"
        if len(first_number) == 4:
            return f"%Y{sep}%m{sep}%d"
        else:
            raise ValueError(f"Invalid date '{value}'.")

    @staticmethod
    def extract_in_full_date(value, default_year=CURRENT_YEAR) -> date:
        """
        >>> NormalizationUtils.extract_numeric_date("10 de fevereiro de 2022.pdf")
        datetime.date(2022, 2, 10)
        >>> NormalizationUtils.extract_numeric_date("07 janeiro de 2022.pdf", default_year=2021)
        datetime.date(2022, 1, 7)
        >>> NormalizationUtils.extract_numeric_date("25 de Novembro", default_year=2020)
        datetime.date(2020, 11, 25)
        >>> NormalizationUtils.extract_numeric_date("blabla 24 de julho de 2021")
        datetime.date(2021, 07, 24)
        >>> NormalizationUtils.extract_numeric_date("19 de Fevereiro de 2022, às 13:01")
        datetime.date(2022, 02, 19)
        """
        result = REGEXP_IN_FULL_DATE.findall(value)
        if result:
            day, month, year = result[0]
            year = int(year) if year else default_year
            year = year if year > 2000 else 2000 + year
            month = NormalizationUtils.month_name_to_number(month)
            return date(year, month, int(day))

    @staticmethod
    def extract_numeric_date(value) -> date:
        """
        >>> NormalizationUtils.extract_numeric_date("some text 30-11-21.pdf")
        datetime.date(2021, 11, 30)
        >>> NormalizationUtils.extract_numeric_date("30-11-2021(1).pdf")
        datetime.date(2021, 11, 30)
        >>> NormalizationUtils.extract_numeric_date("PUBLICADO ÀS 13:00 do dia 30/11/2021")
        datetime.date(2021, 11, 30)
        >>> NormalizationUtils.extract_numeric_date("30/11/21")
        datetime.date(2021, 11, 30)
        >>> NormalizationUtils.extract_numeric_date("29-11")
        None
        """
        result = REGEXP_NUMERIC_DATE.findall(value)
        if result:
            day, month, year = result[0]
            year = int(year)
            year = year if year > 2000 else 2000 + year
            return date(year, int(month), int(day))

    @staticmethod
    def remove_accentuation(original_text):
        return (
            unicodedata.normalize("NFKD", original_text)
            .encode("ascii", errors="ignore")
            .decode("ascii")
        )

    @staticmethod
    def month_name_to_number(month_name):
        try:
            return MONTHS.index(month_name.lower()[:3]) + 1
        except ValueError:
            raise ValueError(f'"{month_name}" is not a valid month name.')


class RowsPtBrIntegerField(rows.fields.IntegerField):
    """IntegerField which removes `.` (thousands separator in Portuguese)"""

    @classmethod
    def deserialize(cls, value):
        return super().deserialize(value.replace(".", "").replace(",", "."))
