import csv
import io

import scrapy


class ConsolidaSpider(scrapy.Spider):
    name = "consolida"

    def __init__(self, input_filename):
        self.input_filename = input_filename

    def start_requests(self):
        with open(self.input_filename) as fobj:
            reader = csv.DictReader(fobj)
            for row in reader:
                yield scrapy.Request(
                    row["csv_url"],
                    meta={"row": row},
                )

    def parse(self, response):
        reader = csv.DictReader(io.StringIO(response.body_as_unicode()))
        for row in reader:
            yield row
