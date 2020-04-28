import csv
import io
from pathlib import Path

import rows
import scrapy
from cached_property import cached_property


BASE_PATH = Path(__file__).parent.parent.parent
POPULATION_PATH = BASE_PATH / "data" / "populacao-estimada-2019.csv"


class BaseCovid19Spider(scrapy.Spider):
    def __init__(self, fobj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fobj = fobj
        self.data = []

    def write_row(self, row):
        self.data.append(row)

    @cached_property
    def brazilian_population(self):
        return rows.import_from_csv(POPULATION_PATH)

    def state_population(self, state):
        return [row for row in self.brazilian_population if row.state == state]

    @cached_property
    def population(self):
        return self.state_population(self.name)

    @cached_property
    def city_id_from_name(self):
        data = {row.city: int(row.city_ibge_code) for row in self.population}
        data[rows.fields.slug("Importados/Indefinidos")] = None
        return data

    def get_city_id_from_name(self, name):
        return {
            rows.fields.slug(key): value
            for key, value in self.city_id_from_name.items()
        }[rows.fields.slug(name)]

    @cached_property
    def city_name_from_id(self):
        data = {int(row.city_ibge_code): row.city for row in self.population}
        data[None] = "Importados/Indefinidos"
        return data

    def get_city_name_from_id(self, city_id):
        return self.city_name_from_id[city_id]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=scrapy.signals.spider_closed)
        return spider

    @property
    def normalized_data(self):
        def order_function(row):
            if row["municipio"] == "TOTAL NO ESTADO":
                return "0"
            elif row["municipio"] == "Importados/Indefinidos":
                return "1"
            else:
                return rows.fields.slug(row["municipio"])
        return sorted(self.data, key=order_function)

    def spider_closed(self, spider):
        data = self.normalized_data
        print(data)
        first_row = data[0]
        writer = csv.DictWriter(self.fobj, fieldnames=list(first_row.keys()))
        writer.writeheader()
        for row in data:
            writer.writerow(row)
