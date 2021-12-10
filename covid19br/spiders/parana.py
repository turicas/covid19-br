import csv
import datetime
import io
from collections import defaultdict

from lxml.html import document_fromstring
from rows.utils.date import date_range
import requests
import rows


class PtBrIntegerField(rows.fields.IntegerField):
    """IntegerField which removes `.` (thousands separator in Portuguese)"""

    @classmethod
    def deserialize(cls, value):
        return super().deserialize(value.replace(".", "").replace(",", "."))


class PtBrDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"


def download_csv(url):
    """Download and parse CSV bulletin"""

    response = requests.get(url)
    if not response.ok:
        raise RuntimeError(f"CSV bulletin not found: {url}")
    return rows.import_from_csv(
        io.BytesIO(response.content),
        encoding="utf-8-sig",
        dialect="excel-semicolon",
        force_types={
            "casos": rows.fields.IntegerField,
            "obitos": rows.fields.IntegerField,
        },
    )


def bulletins_list():
    """List bulletins' CSV and PDF URLs for each date"""

    url = "https://www.saude.pr.gov.br/Pagina/Coronavirus-COVID-19"
    response = requests.get(url)
    tree = document_fromstring(response.text)
    result = defaultdict(dict)

    filetype_divs = {
        "csv": tree.xpath("//div[contains(@class, 'row row-') and contains(.//a//text(), 'Casos e Óbitos') and contains(.//a/@href, '.csv')]"),
        "pdf": tree.xpath("//div[contains(@class, 'row row-') and contains(.//a//text(), 'Informe Completo') and contains(.//a/@href, '.pdf')]"),
    }
    for filetype, divs in filetype_divs.items():
        for div in divs:
            date = PtBrDateField.deserialize(div.xpath(".//p//text()")[0], "%d/%m/%Y")
            url = div.xpath(".//a/@href")[0]
            result[date][filetype] = url

    return result


def extract_outside_state(pdf_url):
    """Extract imported (outside state) cases and deaths from PDF bulletin

    The information is always on the last page, after 'RESIDENTES FORA DO PARANÁ'.
    """

    response = requests.get(pdf_url)
    last_page = rows.plugins.pdf.number_of_pages(io.BytesIO(response.content))
    doc = rows.plugins.pdf.PyMuPDFBackend(io.BytesIO(response.content))
    table = rows.import_from_pdf(
        io.BytesIO(response.content),
        page_numbers=(last_page,),
        starts_after="RESIDENTES FORA DO PARANÁ",
        force_types={
            "casos": PtBrIntegerField,
            "obitos": PtBrIntegerField,
        },
    )
    for row in table:
        if row.fora_do_pr == "TOTAL":
            return row.casos, row.obitos
    raise RuntimeError("Informação não encontrada")


def state_totals(date=None):
    """Extract state total cases and deaths, including imported ones (outside of state)"""

    bulletins_urls = bulletins_list()
    if date is not None:
        urls = bulletins_urls[date]
    else:  # Get the latest PDF and CSV URLs for the most recent date
        for date in sorted(bulletins_urls.keys(), reverse=True):
            urls = bulletins_urls[date]
            if "pdf" in urls and "csv" in urls:
                break

    # Regular cases
    cases, deaths = 0, 0
    for row in download_csv(urls["csv"]):
        cases += row.casos
        deaths += row.obitos

    # Outside state cases
    cases_outside, deaths_outside = extract_outside_state(urls["pdf"])

    return date, cases + cases_outside, deaths + deaths_outside

def create_csv(filename, csv_url, pdf_url):
    total_cases, total_deaths = 0, 0
    writer = rows.utils.CsvLazyDictWriter(filename)

    for row in download_csv(csv_url):
        total_cases += row.casos
        total_deaths += row.obitos
        writer.writerow({"municipio": row.municipio, "confirmados": row.casos, "mortes": row.obitos})

    imported_cases, imported_deaths = extract_outside_state(pdf_url)
    writer.writerow({"municipio": "Importados/Indefinidos", "confirmados": imported_cases, "mortes": imported_deaths})
    total_cases += imported_cases
    total_deaths += imported_deaths

    writer.writerow({"municipio": "TOTAL NO ESTADO", "confirmados": total_cases, "mortes": total_deaths})
    writer.close()


def create_csvs(start_date, end_date, filename_pattern):
    print(f"Downloading bulletins list...")
    bulletins = bulletins_list()
    for date in date_range(start_date, end_date):
        if date not in bulletins:
            print(f"Skipping {date}: not in bulletins list.")
            continue
        urls = bulletins[date]
        if "pdf" not in urls or "csv" not in urls:
            print(f"Skipping {date}: missing CSV or PDF url.")
            continue

        print(f"Creating CSV for {date} based on:")
        print(f"  {urls['csv']}")
        print(f"  {urls['pdf']}")
        create_csv(filename_pattern.format(date=date), urls["csv"], urls["pdf"])


if __name__ == "__main__":
    import argparse
    import datetime

    parser = argparse.ArgumentParser()
    parser.add_argument("start_date")
    parser.add_argument("end_date")
    parser.add_argument("filename_pattern")
    args = parser.parse_args()

    parse_date = lambda value: datetime.datetime.strptime(value, "%Y-%m-%d").date()

    create_csvs(
        parse_date(args.start_date),
        parse_date(args.end_date),
        args.filename_pattern,
    )
