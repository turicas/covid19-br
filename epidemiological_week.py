import datetime

import rows

from date_utils import brazilian_epidemiological_week, date_range, one_day


def generate_epidemiological_week_file(start_date, end_date, filename):
    writer = rows.utils.CsvLazyDictWriter(filename)
    for date in date_range(start_date, end_date + one_day):
        year, week = brazilian_epidemiological_week(date)
        row = {"date": date, "epidemiological_year": year, "epidemiological_week": week}
        writer.writerow(row)


if __name__ == "__main__":
    start_date = datetime.date(2012, 1, 1)
    end_date = datetime.date(2021, 12, 31)
    filename = "data/epidemiological-week.csv"

    generate_epidemiological_week_file(start_date, end_date, filename)
