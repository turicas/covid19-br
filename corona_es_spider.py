import io
from datetime import datetime, date
from urllib.parse import urljoin, parse_qs, urlparse

import rows
import scrapy


class CoronaESSpider(scrapy.Spider):
    name = "corona-es"

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
                urljoin(response.url, boletim),
                callback=self.parse_boletim,
            )

        pages = response.xpath("//ul[@class = 'pager']//a/@href").extract()
        for page_url in pages:
            parsed_qry_str = parse_qs(urlparse(page_url).query)
            if parsed_qry_str.get('page'):
                page_number = int(parse_qs(urlparse(page_url).query)["page"][0])
                if current_page + 1 == page_number:
                    yield scrapy.Request(
                        urljoin(response.url, page_url),
                        callback=self.parse_page,
                        meta={"page": current_page + 1},
                    )

    def parse_boletim(self, response):
        published_date = response.xpath('//*[@id="layout-wrapper"]/div[3]/div/article/div/div/div/header/div/div[1]/div/div/text()[1]').get()
        published_date = published_date.strip().split(' ')[0]

        published_date = datetime.strptime(published_date, '%d/%m/%Y').date()

        if published_date >= date(2020, 3, 19):
            table = rows.import_from_html(io.BytesIO(response.body))
            for row in table:
                yield dict(row._asdict())  # TODO: convert to our format

