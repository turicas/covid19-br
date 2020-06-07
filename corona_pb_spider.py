import re

import scrapy


class PBSpider(scrapy.Spider):
    name = "PB"

    def start_requests(self):
        urls = [
            'https://paraiba.pb.gov.br/diretas/saude/coronavirus/noticias',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for raw_url in response.css('.url'):
            url = raw_url.attrib['href']

            if url.startswith('https://paraiba.pb.gov.br/diretas/saude/coronavirus/noticias/atualizacao-covid-19'):
                yield response.follow(url, self.parse)

        paragraphs = response.css('p')

        yield {
            "date": self.__get_date(paragraphs),
            "deaths": self.__get_total_deaths(paragraphs),
            "confirmed": self.__get_total_cases(paragraphs)
        }

    def __get_date(self, response):
        cell_text = response.css('.documentFirstHeading').get()
        day_and_month = re.search('[0-9]+\/[0-9]+\/', cell_text).group(0)

        return f'{day_and_month}2020'

    def __get_total_cases(self, paragraphs):
        cell_text, *_ = self.__get_confirmed_paragraph(paragraphs)

        return self.__extract_number(cell_text)

    def __get_confirmed_paragraph(self, paragraphs):
        return [p.get() for p in paragraphs if 'Casos Confirmados' in p.get()] or \
               [p.get() for p in paragraphs if 'TOTAL CONFIRMADOS' in p.get()]

    def __get_total_deaths(self, paragraphs):
        cell_text, *_ = self.__get_deaths_paragraph(paragraphs)

        return self.__extract_number(cell_text)

    def __get_deaths_paragraph(self, paragraphs):
        return [p.get() for p in paragraphs if 'Óbitos confirmados' in p.get()] or \
               [p.get() for p in paragraphs if 'TOTAL DE ÓBITOS' in p.get()]

    def __extract_number(self, text_cell):
        raw_number = re.search('[0-9]+\.?[0-9]+', text_cell).group(0)
        return int(raw_number.replace('.', ''))
