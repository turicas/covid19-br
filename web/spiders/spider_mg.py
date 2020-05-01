import io
import rows
from itertools import groupby
import datetime

from .base import BaseCovid19Spider

class PtBrDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"

class MGSpider(BaseCovid19Spider):
    name = "MG"
    start_urls = ["http://www.saude.mg.gov.br/images/noticias_e_eventos/000_2020/coronavirus-dados-csv/notificacoes-covid19-mg.csv"]

    def parse(self, response):
        # Read the csv
        encoding = "utf-8"
        # Could use force_types here.
        table  = rows.import_from_csv(
            io.BytesIO(response.body),
            encoding=encoding
            )

        # Filter the table to only have confirmed cases
        table = [row for row in table if "Confirmado" in row.classificacao_caso]

        # The last report date
        last_date = datetime.datetime.strptime(str(table[0].data_atualizacao), "%Y-%m-%d").strftime('%d/%m/%y')

        row_key = lambda r: r.municipio_residencia
        table.sort(key=row_key)

        total_confirmed = total_deaths = 0
        imported_confirmed = imported_deaths = None

        for city, cases in groupby(table, key=row_key):
            cases = list(cases)
            confirmed = len(cases)
            deaths = sum([1 for c in cases if "óbito" in c.classificacao_caso.lower()])

            try:
                self.get_city_id_from_name(city)
            except KeyError:
                imported_confirmed = (imported_confirmed or 0) + confirmed
                imported_deaths = (imported_deaths or 0) + deaths
            else:
                self.add_city_case(city=city, confirmed=confirmed, deaths=deaths)

            total_confirmed += confirmed
            total_deaths += deaths

        self.add_state_case(confirmed=total_confirmed, deaths=total_deaths)
        self.add_city_case(
            city="Importados/Indefinidos",
            confirmed=imported_confirmed,
            deaths=imported_deaths,
        )