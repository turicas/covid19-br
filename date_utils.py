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
def brazilian_epidemiological_week(year, date):
    """
    >>> brazilian_epidemiological_week(2019, datetime.date(2019, 1, 1))
    1
    >>> brazilian_epidemiological_week(2019, datetime.date(2019, 1, 6))
    2
    >>> brazilian_epidemiological_week(2019, datetime.date(2019, 12, 28))
    52
    >>> brazilian_epidemiological_week(2020, datetime.date(2020, 1, 1))
    1
    >>> brazilian_epidemiological_week(2020, datetime.date(2020, 1, 5))
    2
    >>> brazilian_epidemiological_week(2020, datetime.date(2020, 12, 27))
    53
    """
    start_dates = {
        2017: datetime.date(2017, 1, 1),
        2018: datetime.date(2017, 12, 31),
        2019: datetime.date(2018, 12, 30),
        2020: datetime.date(2019, 12, 29),
    }
    # TODO: add last dates for each year
    start_date = start_dates[year]
    week_range = date_range(start_date, date + 366 * one_day, interval="weekly")
    for count, start in enumerate(week_range, start=1):
        end = start + 6 * one_day
        if start <= date <= end:
            return count
