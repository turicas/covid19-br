import io
from urllib.parse import urljoin, parse_qs, urlparse

import rows
import scrapy


class CoronaESSpider(scrapy.Spider):

    def start_requests(self):
        yield scrapy.Request(
            "https://coronavirus.es.gov.br/Noticias",
            callback=self.parse_page,
            meta={"page": 1},
        )

    def parse_page(self, response):
        current_page = response.meta["page"]
        for boletim in response.xpath("//a[contains(text(), 'boletim')]/@href").extract():
            yield scrapy.Request(
                boletim,
                callback=self.parse_boletim,
            )

        pages = response.xpath("//ul[@class = 'pager']//a/@href").extract()
        for page_url in pages:
            page_number = int(parse_qs(urlparse(page_url).query)["page"][0])
            if current_page + 1 == page_number:
                yield scrapy.Request(
                    urljoin(response.url, page_url),
                    callback=self.parse_page,
                    meta={"page": current_page + 1},
                )

    def parse_boletim(self, response):
        # TODO: parse published date
        # TODO: parse only if date >= 2020-03-19 (city names start on this date)
        table = rows.import_from_html(io.BytesIO(response.body))
        for row in table:
            yield row._asdict()  # TODO: convert to our format

