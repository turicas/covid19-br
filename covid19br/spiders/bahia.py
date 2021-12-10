import datetime
import re

import scrapy


REGEXP_CASES = re.compile("([0-9.]+) casos confirmados")
REGEXP_DEATHS = re.compile("([0-9.]+) tiveram óbito confirmado")


def extract_int(value):
    return int(value.replace(".", ""))


def extract_datetime(value):
    return datetime.datetime.strptime(value, "%d/%m/%Y %H:%M")


class BahiaCovid19TotalSpider(scrapy.Spider):
    start_urls = ["http://www.saude.ba.gov.br/category/emergencias-em-saude/"]

    def __init__(self, result):
        super().__init__(self)
        self.result = result

    def parse(self, response):
        for div in response.xpath("//div[@class = 'noticia']"):
            datahora = extract_datetime(div.xpath(".//p[@class = 'data-hora']/text()").extract()[0])
            titulo = div.xpath(".//h2//text()").extract()[0]
            link = div.xpath(".//h2/a/@href").extract()[0]
            if "bahia" in titulo.lower() and "covid" in titulo.lower():
                yield scrapy.Request(
                    link,
                    callback=self.parse_bulletin_text,
                    meta={"row": {"data": datahora.date()}},
                )

    def parse_bulletin_text(self, response):
        meta = response.meta["row"]
        html = response.text
        cases = REGEXP_CASES.findall(html)
        deaths = REGEXP_DEATHS.findall(html)
        if cases and deaths:
            self.result.append({
                "data": meta["data"],
                "confirmados": extract_int(cases[0]),
                "mortes": extract_int(deaths[0]),
            })


if __name__ == "__main__":
    import rows
    from scrapy.crawler import CrawlerProcess


    result = []
    process = CrawlerProcess(settings={})
    process.crawl(BahiaCovid19TotalSpider, result=result)
    process.start()

    result.sort(reverse=True, key=lambda row: row["data"])
    print(rows.export_to_txt(rows.import_from_dicts(result)))
