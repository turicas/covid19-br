import datetime

from .base import BaseCovid19Spider


class Covid19SESpider(BaseCovid19Spider):
    name = "SE"
    start_urls = ["https://todoscontraocorona.net.br/"]

    def parse(self, response):
        last_updated = self._parse_last_updated(response)
        table_rows = response.xpath("//table[@id='footable_4258']//tr")

        cases = [
            self._parse_row(row.xpath("td/text()").extract())
            for row in table_rows[1:]
        ]

        assert cases[0]["municipio"] == "Amparo de São Francisco", cases[0]
        assert cases[37]["municipio"] == "Maruim", cases[37]
        assert cases[-1]["municipio"] == "Umbaúba", cases[-1]

        self.add_cases(cases, last_updated)

    def add_cases(self, cases, last_updated):
        self.add_report(date=last_updated, url=self.start_urls[0])

        total_no_estado = 0
        obitos = 0
        for case in cases:
            self.add_city_case(
                city=case["municipio"],
                confirmed=case["confirmado"],
                deaths=case["obito"]
            )
            total_no_estado += case["confirmado"]
            obitos += case["obito"]

        self.add_state_case(confirmed=total_no_estado, deaths=obitos)

    def _parse_row(self, row):
        def _parse_float(num):
            return float(num.replace(",", "."))

        column_types = {
            "municipio": str,
            "confirmado": int,
            "obito": int,
            "letalidade": _parse_float,
            "incidencia_por_100000_habitantes": _parse_float,
            "mortalidade_por_100000_habitantes": _parse_float,
            "isolamento_social": lambda num: int(num.replace("%", "")) / 10,
        }
        
        return {
            key: cast_func(column)
            for ((key, cast_func), column) in zip(column_types.items(), row)
        }

    def _parse_last_updated(self, response):
        text = response.xpath("//div[@id='texto-atualizacao']//strong/text()").extract()
        last_updated = datetime.datetime.strptime(text[0].split()[0], "%d/%m/%y")
        return last_updated.date()
