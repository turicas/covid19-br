from datetime import datetime
import io
import scrapy
import rows

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import State
from covid19br.common.models.bulletin_models import CountyBulletinModel


EXPRESSION_FOR_DEATH_PLUS_CONFIRMED_CASES = "Distribuição dos casos e óbitos confirmados acumulados"


class SpiderTO(BaseCovid19Spider):
    state = State.TO
    name = State.TO.value

    start_urls = ["https://www.to.gov.br/saude/boletim-covid-19/3vvgvo8csrl6"]

    def parse(self, response, **kwargs):
        bulletins_per_date = {}
        bulletins = response.xpath(
            '//div[contains(@class, "page_extra_files")]//ul//a[contains(@href, "/download/")]'
        )
        for bulletin in bulletins:
            pdf_url = bulletin.xpath(".//@href").get()
            date = self._extract_date(bulletin)
            bulletins_per_date[date] = pdf_url

        for date in self.dates_range:
            url = bulletins_per_date.get(date)
            if url:
                yield scrapy.Request(
                    url, callback=self.parse_pdf, cb_kwargs={"date": date}
                )

    def parse_pdf(self, response, date):
        """Converte PDF do boletim COVID-19 do Tocantins em CSV"""
        doc = rows.plugins.pdf.PyMuPDFBackend(io.BytesIO(response.body))
        all_pages_numbers = range(1, rows.plugins.pdf.number_of_pages(io.BytesIO(response.body)) + 1)
        for page_number in all_pages_numbers:
            page_content = list(next(doc.text_objects(page_numbers=(page_number,))))
            page_text = "\n".join(obj.text for obj in page_content)

            if EXPRESSION_FOR_DEATH_PLUS_CONFIRMED_CASES in page_text:
                for city, cases, deaths in self._extract_table_data_with_cases_and_deaths(page_content):
                    bulletin = CountyBulletinModel(
                        date=date,
                        state=self.state,
                        city=city,
                        confirmed_cases=cases,
                        deaths=deaths,
                        source_url=response.request.url,
                    )
                    self.add_new_bulletin_to_report(bulletin, date)

    def _extract_table_data_with_cases_and_deaths(self, page_content):
        """Extrai as tabelas contidas nos objetos"""

        # Pega posição x do meio dos títulos (cabeçalhos) das tabelas
        cities_boundaries, cases_boundaries, death_boundaries = [], [], []
        for obj in sorted(page_content, key=lambda obj: (obj.y0, obj.x0)):
            if obj.text == "MUNICÍPIO":
                cities_boundaries.append(int(obj.x0 + (obj.x1 - obj.x0) / 2))
            elif obj.text == "CASOS":
                cases_boundaries.append(int(obj.x0 + (obj.x1 - obj.x0) / 2))
            elif obj.text == "ÓBITOS":
                death_boundaries.append(int(obj.x0 + (obj.x1 - obj.x0) / 2))
        # Como são 2 colunas (1 com pelo menos 1 tabela), devemos pegar as
        # coordenadas da tabela mais à esquerda e da mais à direita:
        first_cities, last_cities = min(cities_boundaries), max(cities_boundaries)
        first_cases, last_cases = min(cases_boundaries), max(cases_boundaries)
        first_deaths, last_deaths = min(death_boundaries), max(death_boundaries)

        # Organiza os objetos em lista de municípios e valor numérico, de acordo
        # com suas posições x
        cities, cases, deaths = [], [], []
        for obj in page_content:
            if obj.x0 < first_cities < obj.x1 or obj.x0 < last_cities < obj.x1:
                cities.append(obj)
            elif obj.x0 < first_cases < obj.x1 or obj.x0 < last_cases < obj.x1:
                cases.append(obj)
            elif obj.x0 < first_deaths < obj.x1 or obj.x0 < last_deaths < obj.x1:
                deaths.append(obj)

        # Identifica os objetos em tabela da esquerda vs tabela da direita
        # e ordena os objetos selecionados a partir de (y0, x0)
        page_middle_x = (last_deaths - first_cities) / 2 + first_cities
        table_position = lambda obj: 1 if obj.x0 > page_middle_x else 0
        obj_sort = lambda obj: (table_position(obj), obj.y0, obj.x0)
        cities.sort(key=obj_sort)
        cases.sort(key=obj_sort)
        deaths.sort(key=obj_sort)

        # Encontra qual o y0 do objeto mais ao topo da página
        first_y0 = min(obj.y0 for obj in cities if obj.text == "MUNICÍPIO")

        # Remove todos os objetos texto que não sejam valores de interesse (tanto
        # os que podem estar fora das tabelas, quanto os cabeçalhos e valores
        # "fantasma" - números que aparecem invisíveis atrás da tabela) e guarda os
        # nomes de municípios sem acento (às vezes aparecem com acento, às vezes,
        # sem, muitas vezes no mesmo PDF).
        clean_cities = [
            self.normalizer.remove_accentuation(obj.text)
            for obj in cities
            if obj.y0 > first_y0 and obj.text != "MUNICÍPIO" and not obj.text.isdigit()
        ]
        clean_cases = [
            int(obj.text.replace(".", ""))
            for obj in cases
            if obj.y0 > first_y0 and obj.text != "CASOS"
        ]
        clean_deaths = [
            int(obj.text.replace(".", ""))
            for obj in deaths
            if obj.y0 > first_y0 and obj.text != "ÓBITOS"
        ]

        for city, cases, deaths in zip(clean_cities, clean_cases, clean_deaths):
            if city == "TOTAL":
                # Elimina o último registro da tabela, que contém o total
                continue
            yield (city, cases, deaths)

    def _extract_date(self, bulletin):
        raw_date_text = bulletin.xpath(".//span//text()").get() or "".join(bulletin.xpath(".//text()").extract())
        cleaned_date_text = (
            raw_date_text
            .replace("  ", " ")
            .replace("-", " ")
            .replace(".", "")
            .replace("de ", "")
            .replace("(1)", "")
            .replace("pdf", "")
            .replace("file_open", "")
            .replace("BOLETIM COVID", "")
            .strip()
        )
        day, month, *year = cleaned_date_text.split()
        day = self._format_day(day)
        month = self._format_month(month)
        year = self._format_year(year)

        return datetime(year, month, day).date()

    def _format_day(self, day):
        return self.normalizer.ensure_integer(day)

    def _format_month(self, month):
        try:
            return self.normalizer.ensure_integer(month)
        except ValueError:
            return self.normalizer.month_name_to_number(month)

    def _format_year(self, year):
        if not year:
            return 2020
        year = year[0]
        year = self.normalizer.ensure_integer(year)
        return year if year > 2000 else year + 2000
