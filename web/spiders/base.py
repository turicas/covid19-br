import csv
from functools import lru_cache
from pathlib import Path

import rows
import scrapy
from cached_property import cached_property

BASE_PATH = Path(__file__).parent.parent.parent
POPULATION_PATH = BASE_PATH / "data" / "populacao-estimada-2019.csv"


def normalize_city_name(city):
    city = rows.fields.slug(city)
    for word in ("da", "das", "de", "do", "dos"):
        city = city.replace(f"_{word}_", "_")
    return city


class BaseCovid19Spider(scrapy.Spider):
    def __init__(self, report_fobj, case_fobj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_fobj = case_fobj
        self.report_fobj = report_fobj
        self.case_data = []
        self.report_data = []

    def add_report(self, date, url):
        self.report_data.append({"date": date, "url": url})

    def add_city_case(self, city, confirmed, deaths):
        try:
            city_id = self.get_city_id_from_name(city)
            city_name = self.get_city_name_from_id(city_id)
        except KeyError:
            raise ValueError(f"Unknown city '{city}' for state {self.name}")

        self.case_data.append(
            {"municipio": city_name, "confirmados": confirmed, "mortes": deaths}
        )

    def add_state_case(self, confirmed, deaths):
        self.case_data.append(
            {"municipio": "TOTAL NO ESTADO", "confirmados": confirmed, "mortes": deaths}
        )

    @cached_property
    def brazilian_population(self):
        return rows.import_from_csv(POPULATION_PATH)

    @lru_cache(maxsize=900)
    def state_population(self, state):
        return [row for row in self.brazilian_population if row.state == state]

    @cached_property
    def population(self):
        return self.state_population(self.name)

    @cached_property
    def city_id_from_name(self):
        data = {row.city: int(row.city_ibge_code) for row in self.population}
        data["Importados/Indefinidos"] = None
        return data

    @lru_cache(maxsize=900)
    def get_city_id_from_name(self, name):
        normalized_cities = {
            normalize_city_name(key): value
            for key, value in self.city_id_from_name.items()
        }
        return normalized_cities[normalize_city_name(name)]

    @cached_property
    def city_name_from_id(self):
        data = {int(row.city_ibge_code): row.city for row in self.population}
        data[None] = "Importados/Indefinidos"
        return data

    @lru_cache(maxsize=900)
    def get_city_name_from_id(self, city_id):
        return self.city_name_from_id[city_id]

    @property
    def normalized_case_data(self):
        def order_function(row):
            if row["municipio"] == "TOTAL NO ESTADO":
                return "0"
            elif row["municipio"] == "Importados/Indefinidos":
                return "1"
            else:
                return rows.fields.slug(row["municipio"])

        return sorted(self.case_data, key=order_function)

    @property
    def normalized_report_data(self):
        return self.report_data

    def write_csv(self, data, fobj):
        first_row = data[0]
        writer = csv.DictWriter(fobj, fieldnames=list(first_row.keys()))
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(
            spider.spider_closed, signal=scrapy.signals.spider_closed
        )
        return spider

    def spider_closed(self, spider):
        self.write_csv(self.normalized_case_data, self.case_fobj)
        self.write_csv(self.normalized_report_data, self.report_fobj)
