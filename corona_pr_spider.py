"""
A Secretaria de Saúde do Paraná liberou um tipo de boletim ao longo dos
primeiros e dias e outro tipo, mais recentemente:

- O primeiro possui informações específicas sobre cada paciente (se viajou, de
  onde etc.);
- O segundo possui informações gerais sobre casos por município.

Esse script coleta o segundo tipo de boletim.
"""

import os
import re
from pathlib import Path
from urllib.parse import urljoin

import rows
import scrapy
from rows.plugins.plugin_pdf import PyMuPDFBackend, same_column

BASE_PATH = Path(__file__).parent
DOWNLOAD_PATH = BASE_PATH / "data" / "download"
REGEXP_UPDATE = re.compile("Atualização .* ([0-9]{1,2}/[0-9]{1,2}/[0-9]{4}).*")


class PtBrDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"


class PtBrDateField2(rows.fields.DateField):
    INPUT_FORMAT = "%d%m%Y"


class MinX0Backend(PyMuPDFBackend):
    """Filter PDF objects, eliminating first column"""

    name = "min-x0"

    def objects(self, *args, **kwargs):
        kwargs["starts_after"] = re.compile("REGIONAL.*")
        original_objects = [list(page) for page in super().objects(*args, **kwargs)]

        first_column = same_column(original_objects[0], "MUNICÍPIO")
        municipio = [obj for obj in first_column if obj.text == "MUNICÍPIO"][0]
        min_x0 = min(obj.x0 for obj in first_column)
        for page in original_objects:
            yield [obj for obj in page if obj.x0 >= min_x0]


class CleanIntegerField(rows.fields.IntegerField):
    @classmethod
    def deserialize(cls, value):
        value = str(value or "").strip().replace("*", "")
        if not value or value == "-":
            return 0
        else:
            return int(value)


def convert_row(row):
    field_names = "municipio data casos_confirmados casos_descartados casos_suspeitos total boletim_data boletim_url boletim_titulo".split()
    new = {}
    for field_name in field_names:
        value = row.get(field_name, None)
        if value is None and field_name.startswith("casos_"):
            value = row.get(field_name.replace("casos_", ""), None)
        if field_name in (
            "casos_confirmados",
            "casos_descartados",
            "casos_suspeitos",
            "total",
        ):
            value = CleanIntegerField.deserialize(value)
        new[field_name] = value

    if new["data"] != new["boletim_data"]:
        print(
            f"Data do boletim {new['boletim_data']} é diferente da data do PDF {new['data']}"
        )

    city = new["municipio"].strip()
    if not city:  # "TOTAL" is present. Skip it.
        return None

    return {
        "date": new["data"],
        "state": "PR",
        "city": city,
        "place_type": "city",
        "notified": new["total"],
        "confirmed": new["casos_confirmados"],
        "discarded": new["casos_descartados"],
        "suspect": new["casos_suspeitos"],
        "deaths": "",  # TODO: fix
        "notes": "",
        "source_url": new["boletim_url"],
    }


def parse_pdf(filename, meta):
    # Extract update date
    pdf_doc = PyMuPDFBackend(filename)
    update_date = None
    for page in pdf_doc.objects():
        for obj in page:
            if REGEXP_UPDATE.match(obj.text):
                update_date = PtBrDateField.deserialize(
                    REGEXP_UPDATE.findall(obj.text)[0]
                )
                break
    if update_date is None:  # String not found in PDF
        # Parse URL to get date inside PDF's filename
        date = (
            meta["boletim_url"]
            .split("/")[-1]
            .split(".pdf")[0]
            .replace("CORONA_", "")
            .split("_")[0]
        )
        update_date = PtBrDateField2.deserialize(date)

    # Extract rows and inject update date and metadata
    table = rows.import_from_pdf(filename, backend="min-x0")
    for row in table:
        if row.municipio == "TOTAL GERAL":
            continue
        row = row._asdict()
        row["data"] = update_date
        row.update(meta)
        yield convert_row(row)


class CoronaPrSpider(scrapy.Spider):
    name = "corona-pr"
    start_urls = [
        "http://www.saude.pr.gov.br/modules/conteudo/conteudo.php?conteudo=3507"
    ]

    def parse(self, response):
        for link in response.xpath("//a[contains(@href, '.pdf')]"):
            data = {
                "boletim_titulo": link.xpath(".//text()").extract_first(),
                "boletim_url": urljoin(
                    response.url, link.xpath(".//@href").extract_first()
                ),
            }
            if not data["boletim_titulo"].lower().startswith("boletim"):
                continue
            data["boletim_data"] = PtBrDateField.deserialize(
                data["boletim_titulo"].split()[1]
            )

            yield scrapy.Request(
                url=data["boletim_url"], meta={"row": data}, callback=self.parse_pdf,
            )

    def parse_pdf(self, response):
        filename = DOWNLOAD_PATH / Path(response.url).name
        with open(filename, mode="wb") as fobj:
            fobj.write(response.body)

        meta = response.meta["row"]
        pdf_doc = rows.plugins.pdf.PyMuPDFBackend(filename)
        pdf_text = "".join(item for item in pdf_doc.extract_text() if item.strip())

        if pdf_text and "CLASSIFICAÇÃO\nFINAL" not in pdf_text:
            # This is a new-style PDF, which has the data we want

            result = []
            for row in parse_pdf(filename, meta):
                if row is not None:
                    result.append(row)
            result.append(
                {
                    "date": result[0]["date"],
                    "state": "PR",
                    "city": "",
                    "place_type": "state",
                    "notified": sum(row["notified"] for row in result),
                    "confirmed": sum(row["confirmed"] for row in result),
                    "discarded": sum(row["discarded"] for row in result),
                    "suspect": sum(row["suspect"] for row in result),
                    "deaths": "",  # TODO: fix
                    "notes": "",
                    "source_url": result[0]["source_url"],
                }
            )
            result.sort(key=lambda row: row["city"])
            for row in result:
                yield row

        else:
            # Old style PDFs are not parsed and should be removed from disk
            # Old styles are PDFs which:
            # - Have an image, no text
            # - Patient data (not number of cases per city)
            os.unlink(filename)
