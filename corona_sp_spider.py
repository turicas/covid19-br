import csv
import datetime
import io

import rows
import scrapy


class SPSpider(scrapy.Spider):
    name = "SP"
    state_ibge_code = 35
    start_urls = ["https://www.seade.gov.br/coronavirus/"]

    def parse(self, response):
        self.cities = {
            row.city_ibge_code: row
            for row in rows.import_from_csv("data/populacao-estimada-2019.csv")
            if row.state == "SP"
        }
        csv_url = response.xpath(
            "//a[contains(@href, '.csv') and contains(strong/text(), 'Municípios')]/@href"
        ).extract_first()
        yield scrapy.Request(csv_url, callback=self.parse_csv)

    def parse_csv(self, response):
        reader = csv.DictReader(
            io.StringIO(response.body.decode("iso-8859-1")), delimiter=";"
        )
        city_name_key = "Município"
        city_code_key = "Cód IBGE"
        confirmed_key = "Mun_Total de casos"
        deaths_key = "Mun_Total de óbitos"
        now = datetime.datetime.now()
        today = datetime.date(now.year, now.month, now.day)
        total_confirmed = total_deaths = 0
        for row in reader:
            city = row[city_name_key]
            city_ibge_code = int(row[city_code_key]) if row[city_code_key] else None
            confirmed = int(row[confirmed_key])
            deaths = int(row[deaths_key])
            if city == "Outros países":
                confirmed_imported = confirmed
                deaths_imported = deaths
                continue
            elif city == "Ignorado":
                confirmed_undefined = confirmed
                deaths_undefined = deaths
                continue
            elif city == "Outros estados":
                confirmed_other_states = confirmed
                deaths_other_states = deaths
                continue
            else:
                city = self.cities[city_ibge_code]
                total_confirmed += confirmed
                total_deaths += deaths
                yield {
                    "city": city.city,
                    "city_ibge_code": city_ibge_code,
                    "confirmed": confirmed,
                    "date": today,
                    "deaths": deaths,
                    "place_type": "city",
                    "state": self.name,
                }

        confirmed = confirmed_imported + confirmed_undefined + confirmed_other_states
        deaths = deaths_imported + deaths_undefined + deaths_other_states
        total_confirmed += confirmed
        total_deaths += deaths
        yield {
            "city": "Importados/Indefinidos",
            "city_ibge_code": None,
            "confirmed": confirmed,
            "date": today,
            "deaths": deaths,
            "place_type": "city",
            "state": self.name,
        }
        yield {
            "city": None,
            "city_ibge_code": self.state_ibge_code,
            "confirmed": total_confirmed,
            "date": today,
            "deaths": total_deaths,
            "place_type": "state",
            "state": self.name,
        }
