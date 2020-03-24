import io
from datetime import date, datetime
from urllib.parse import parse_qs, urljoin, urlparse

import rows
import scrapy
from bs4 import BeautifulSoup


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
        boletins = response.xpath(
            "//a[contains(text(), 'boletim')]/@href"
        ).extract()
        for boletim in boletins:
            yield scrapy.Request(
                urljoin(response.url, boletim), callback=self.parse_boletim,
            )

        pages = response.xpath("//ul[@class = 'pager']//a/@href").extract()
        for page_url in pages:
            parsed_qry_str = parse_qs(urlparse(page_url).query)
            if parsed_qry_str.get("page"):
                page_number = int(parse_qs(urlparse(page_url).query)["page"][0])
                if current_page + 1 == page_number:
                    yield scrapy.Request(
                        urljoin(response.url, page_url),
                        callback=self.parse_page,
                        meta={"page": current_page + 1},
                    )

    def parse_boletim(self, response):
        published_date = response.xpath(
            '//*[@id="layout-wrapper"]/div[3]/div/article/div/div/div/header/div/div[1]/div/div/text()[1]'
        ).get()
        published_date = published_date.strip().split(" ")[0]

        published_date = datetime.strptime(published_date, "%d/%m/%Y").date()

        cases = ()

        if published_date >= date(2020, 3, 19):
            if published_date >= date(2020, 3, 23):
                cases = parse_03_23(published_date, response.body, response.url)

            if published_date == date(2020, 3, 22):
                cases = parse_03_22(published_date, response.body, response.url)

            if published_date <= date(2020, 3, 21):
                cases = parse_03_21(published_date, response.body, response.url)

        for case in cases:
            yield case


def parse_03_23(date, response_body, url):
    table = rows.import_from_html(io.BytesIO(response_body))
    output = []

    for row in table:
        row_dict = row._asdict()
        if row_dict["municipio_de_residencia"] != "TOTAL GERAL":
            if row_dict["casos_confirmados"] > 0:
                output.append(
                    to_sheet_format(
                        date=date,
                        city=row_dict["municipio_de_residencia"],
                        place_type="city",
                        confirmed=row_dict["casos_confirmados"],
                        death="",
                        url=url,
                    )
                )
        else:
            output.append(
                to_sheet_format(
                    date=date,
                    city="",
                    place_type="state",
                    confirmed=row_dict["casos_confirmados"],
                    death="",
                    url=url,
                )
            )

    return output


def parse_03_22(date, response_body, url):
    table_data = [
        [cell.text for cell in row("td")]
        for row in BeautifulSoup(response_body, features="lxml")("tr")
    ]
    output = []
    for row in table_data:
        if (len(row) > 1 and row[0] != ""):
            row = [col.strip() for col in row]
            if row[0] not in ("Total", "Total Geral") and row[-1] != "Total":
                if row[1] != "0":
                    output.append(
                        to_sheet_format(
                            date=date,
                            city=row[0],
                            place_type="city",
                            confirmed=row[1],
                            death="",
                            url=url,
                        )
                    )
            if row[0] == "Total Geral":
                output.append(
                    to_sheet_format(
                        date=date,
                        city="",
                        place_type="state",
                        confirmed=row[1],
                        death="",
                        url=url,
                    )
                )

    return output


def parse_03_21(date, response_body, url):
    table_data = [
        [cell.text for cell in row("td")]
        for row in BeautifulSoup(response_body, features="lxml")("tr")
    ]
    output = []

    for row in table_data:
        row = [col.strip() for col in row if row[0]]

        if row[0] == "Região":
            continue

        if row[0] != "TOTAL":
            fixed_row = row[1:] if len(row) == 6 else row
            if fixed_row[4] != "0":
                output.append(
                    to_sheet_format(
                        date=date,
                        city=row[0],
                        place_type="city",
                        confirmed=fixed_row[4],
                        death="",
                        url=url,
                    )
                )
        else:
            output.append(
                to_sheet_format(
                    date=date,
                    city="",
                    place_type="state",
                    confirmed=row[5],
                    death="",
                    url=url,
                )
            )

    return output


def to_sheet_format(date, city, place_type, confirmed, death, url):
    return {
        "date": date.isoformat(),
        "state": "ES",
        "city": city,
        "place_type": place_type,
        "notified": "",
        "confirmed": confirmed,
        "discarded": "",
        "suspect": "",
        "deaths": death,
        "notes": "",
        "source_url": url,
    }
