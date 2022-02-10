import io
from collections import groupby

import rows

from .base import BaseCovid19Spider


class Covid19MGSpider(BaseCovid19Spider):
    name = "MG"
    start_urls = [
        "http://www.saude.mg.gov.br/images/noticias_e_eventos/000_2020/coronavirus-dados-csv/notificacoes-covid19-mg.csv"
    ]

    def parse(self, response):
        table = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding=response.encoding,
            force_types={
                "contador": rows.fields.IntegerField,
                "data_notificacao": rows.fields.DateField,
                "data_atualizacao": rows.fields.DateField,
                "idade": rows.fields.IntegerField,
                "municipio_residencia_cod": rows.fields.IntegerField,
            },
        )

        date = max(row.data_atualizacao for row in table)
        self.add_report(date=date, url=response.url)

        converted_table = []
        last_date = None
        for row in table:
            row = row._asdict()
            row["data_notificacao"] = row["data_notificacao"] or last_date
            last_date = row["data_notificacao"]
            del row["data_atualizacao"]
            converted_table.append(row)
            # TODO: convert row to our "internal" microdata format, like:
            # self.add_microdata_row(self.convert_row_microdata(row))
            # self.add_microdata_row: provided by BaseCovid19Spider
            # self.convert_row_microdata: overriden by child spider classes

        desired_cases = [
            row
            for row in converted_table
            if row["classificacao_caso"] in ("Caso Confirmado", "Óbito Confirmado")
        ]
        row_key = lambda row: row["municipio_residencia_cod"]
        desired_cases.sort(key=row_key)
        total_confirmed = total_deaths = 0
        for city_id, cases in groupby(desired_cases, key=row_key):
            cases = list(cases)
            confirmed = len(cases)
            deaths = sum(
                1 for case in cases if case["classificacao_caso"] == "Óbito confirmado"
            )
            city = self.get_city_name_from_id(city_id)
            self.add_city_case(city=city, confirmed=confirmed, deaths=deaths)
            total_confirmed += confirmed
            total_deaths += deaths

        # TODO: check if we can get values for "Importados/Indefinidos"
        self.add_city_case(city="Importados/Indefinidos", confirmed=None, deaths=None)
        self.add_state_case(confirmed=total_confirmed, deaths=total_deaths)
