import io

import rows

from .base import BaseCovid19Spider


class Covid19RRSpider(BaseCovid19Spider):
    name = "RR"
    start_urls = ["https://roraimacontraocorona.rr.gov.br/winner/public/mapa.xhtml"]

    def parse(self, response):
        table = rows.import_from_html(io.BytesIO(response.body), encoding=response.encoding)
        for row in table:
            if (row.confirmados, row.obitos) == (None, None):
                continue
            city_name = row.cidade
            if city_name.lower().strip() == "total:":
                city_name = "TOTAL NO ESTADO"
            else:
                city_id = self.get_city_id_from_name(city_name)
                city_name = self.get_city_name_from_id(city_id)

            self.write_row({
                "municipio": city_name,
                "confirmados": row.confirmados,
                "mortes": row.obitos or 0,
            })
        self.write_row({
            "municipio": "Importados/Indefinidos",
            "confirmados": None,
            "mortes": None,
        })
