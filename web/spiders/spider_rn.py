import datetime
import io
import os
import re

import rows
import scrapy

from .base import BaseCovid19Spider


def convert_city(city):
    if city in ("TOTAL RN", "MUNICÍPIO DE RESIDÊNCIA"):
        return None
    elif city == "TOTAL OUTRAS LOCALIDADES":
        return "Importados/Indefinidos"
    elif city == "TOTAL GERAL":
        return "TOTAL NO ESTADO"
    else:
        return city


class Covid19RNSpider(BaseCovid19Spider):
    http_proxy = os.environ.get("HTTP_PROXY", None)
    name = "RN"
    start_urls = [
        "http://www.saude.rn.gov.br/Conteudo.asp?TRAN=ITEM&TARG=223456&ACT=&PAGE=&PARM=&LBL=MAT%C9RIA"
    ]

    def parse(self, response):
        yield scrapy.Request(
            url=response.xpath("//a[contains(@href, 'PDF')]/@href")[0].extract(),
            callback=self.parse_pdf,
        )

    def parse_pdf(self, response):
        pdf = rows.plugins.pdf.PyMuPDFBackend(io.BytesIO(response.body))
        pages = pdf.text_objects(starts_after=re.compile("EM INVESTIGAÇÃO.*"))
        found = False
        for page in pages:
            for obj in page:
                if "Dados extraídos" in obj.text:
                    day, month, year = re.compile(
                        "([0-9]{2})/([0-9]{2})/([0-9]{4})"
                    ).findall(obj.text)[0]
                    date = datetime.date(int(year), int(month), int(day))
                    found = True
                    break
            if found:
                break
        self.add_report(date=date, url=response.url)

        table = rows.import_from_pdf(
            io.BytesIO(response.body),
            starts_after=re.compile("DADOS DETALHADOS POR MUNICÍPIO DE RESIDÊNCIA.*"),
            ends_before=re.compile("Fonte:"),
        )
        confirmed_cases = {}
        for row in table:
            city = convert_city(row.municipio_de_residencia)
            if city is None:
                continue
            confirmed = row.casos_confirmados_incidencia_por_n_100_ooo_hab.splitlines()[
                0
            ]
            if confirmed in ("-", ""):
                confirmed = None
            else:
                confirmed = int(confirmed)
            confirmed_cases[city] = confirmed

        table = rows.import_from_pdf(
            io.BytesIO(response.body),
            starts_after=re.compile("EM INVESTIGAÇÃO.*"),
            ends_before=re.compile("Fonte:"),
        )
        deaths_cases = {}
        for row in table:
            city = convert_city(row.field_0)
            if city is None:
                continue
            deaths_cases[city] = int(row.confirmado)

        cities = set(confirmed_cases.keys()) | set(deaths_cases.keys())
        for city in cities:
            confirmed = confirmed_cases.get(city, None)
            deaths = deaths_cases.get(city, None)
            if confirmed is None and deaths is None:
                continue
            confirmed = confirmed or 0
            deaths = deaths or 0
            if confirmed == 0 and deaths == 0:
                continue
            if city == "TOTAL NO ESTADO":
                self.add_state_case(confirmed=confirmed, deaths=deaths)
            else:
                self.add_city_case(city=city, confirmed=confirmed, deaths=deaths)
