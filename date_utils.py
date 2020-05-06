import datetime
from functools import lru_cache

one_day = datetime.timedelta(days=1)


def today():
    date = datetime.datetime.now()
    return datetime.date(date.year, date.month, date.day)


def next_day(date):
    return date + datetime.timedelta(days=1)


def next_week(date):
    return date + datetime.timedelta(days=7)


def next_month(date):
    return datetime.date(
        year=date.year + (date.month // 12), month=(date.month % 12) + 1, day=date.day
    )


def next_date(date, interval="daily"):
    from_interval = {"daily": next_day, "weekly": next_week, "monthly": next_month}

    return from_interval[interval](date)


def date_range(start, stop, interval="daily"):
    current = start
    while current < stop:
        yield current
        current = next_date(date=current, interval=interval)


def date_to_dict(date):
    return {"year": date.year, "month": date.month, "day": date.day}


@lru_cache(4096)
def brazilian_epidemiological_week(date):
    """Calculate Brazilian epidemiological weeks
    Information from:
    <https://portalsinan.saude.gov.br/calendario-epidemiologico-2020/43-institucional>

    >>> brazilian_epidemiological_week(datetime.date(2019, 1, 1))
    (2019, 1)
    >>> brazilian_epidemiological_week(datetime.date(2019, 1, 6))
    (2019, 2)
    >>> brazilian_epidemiological_week(datetime.date(2019, 12, 28))
    (2019, 52)
    >>> brazilian_epidemiological_week(datetime.date(2020, 1, 1))
    (2020, 1)
    >>> brazilian_epidemiological_week(datetime.date(2020, 1, 5))
    (2020, 2)
    >>> brazilian_epidemiological_week(datetime.date(2020, 12, 27))
    (2020, 53)
    >>> brazilian_epidemiological_week(datetime.date(2021, 1, 2))
    (2020, 53)
    """
    dates = {
        2012: {
            "start_date": datetime.date(2012, 1, 1),
            "end_date": datetime.date(2012, 12, 29),
        },
        2013: {
            "start_date": datetime.date(2012, 12, 30),
            "end_date": datetime.date(2013, 12, 28),
        },
        2014: {
            "start_date": datetime.date(2013, 12, 29),
            "end_date": datetime.date(2015, 1, 3),
        },
        2015: {
            "start_date": datetime.date(2015, 1, 4),
            "end_date": datetime.date(2016, 1, 2),
        },
        2016: {
            "start_date": datetime.date(2016, 1, 3),
            "end_date": datetime.date(2016, 12, 31),
        },
        2017: {
            "start_date": datetime.date(2017, 1, 1),
            "end_date": datetime.date(2017, 12, 30),
        },
        2018: {
            "start_date": datetime.date(2017, 12, 31),
            "end_date": datetime.date(2018, 12, 29),
        },
        2019: {
            "start_date": datetime.date(2018, 12, 30),
            "end_date": datetime.date(2019, 12, 28),
        },
        2020: {
            "start_date": datetime.date(2019, 12, 29),
            "end_date": datetime.date(2021, 1, 2),
        },
    }
    year = None
    for possible_year, year_data in dates.items():
        if year_data["start_date"] <= date <= year_data["end_date"]:
            year = possible_year
            break
    if year is None:
        raise ValueError(f"Cannot calculate year for date {date}")

    start_date = dates[year]["start_date"]
    end_date = dates[year]["end_date"]
    week_range = date_range(start_date, end_date + one_day, interval="weekly")
    for count, start in enumerate(week_range, start=1):
        end = start + 6 * one_day
        if start <= date <= end:
            return year, count
