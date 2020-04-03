import io

import rows
import scrapy


class RoraimaSpider(scrapy.Spider):
    name = "rr"
    start_urls = ["https://roraimacontraocorona.rr.gov.br/winner/mapa.xhtml"]

    def parse(self, response):
        date, _ = "".join(item.strip() for item in response.xpath("//div[//h4[contains(text(), 'Última atualização')]]//h6//text()").extract() if item.strip()).split()
        day, month, year = date.split("/")
        date = f"{year}-{int(month):02d}-{int(day):02d}"

        table = rows.import_from_html(io.BytesIO(response.body))
        for row in table:
            place_type = "city" if row.cidade.lower() != "total:" else "state"
            yield {
                "city": row.cidade if place_type == "city" else None,
                "confirmed": row.confirmados,
                "date": date,
                "deaths": row.obitos,
                "discarded": row.descartados,
                "place_type": place_type,
                "recovered": row.curados,
                "state": self.name.upper(),
                "suspect": row.suspeitos,
            }
