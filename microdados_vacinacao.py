import argparse
import csv
import re
import sys
from contextlib import closing
from pathlib import Path
from urllib.request import urlopen

import requests
from lxml.html import document_fromstring
from rows.utils import CsvLazyDictWriter
from tqdm import tqdm

from covid19br.vacinacao import convert_row_censored, convert_row_uncensored


REGEXP_DATE = re.compile("([0-9]{4}-[0-9]{2}-[0-9]{2})")


def get_latest_url_and_date():
    """Scrapes CKAN in order to find the last available CSV for Brazil"""

    repository_url = "https://opendatasus.saude.gov.br/dataset/covid-19-vacinacao/resource/ef3bd0b8-b605-474b-9ae5-c97390c197a8"
    response = urlopen(repository_url)
    html = response.read()
    tree = document_fromstring(html)
    download_url = tree.xpath("//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dados completos')]/@href")[0]
    date = REGEXP_DATE.findall(download_url)[0]
    return download_url, date


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=1_024 * 1_024)
    parser.add_argument("--refresh-count", type=int, default=10_000)
    parser.add_argument("--input-encoding", type=str, default="utf-8")
    args = parser.parse_args()

    # TODO: adicionar opção para selecionar qual dos 3 possíveis CSVs o script
    # irá gerar.
    # TODO: configurar saída do logger para arquivo e não stdout/stderr
    # TODO: adicionar opção para salvar ou não CSV original (compactado)

    url, date = get_latest_url_and_date()
    output_path = Path(__file__).parent / "data" / "output"
    filename_raw = output_path / "microdados_vacinacao-raw.csv.gz"
    filename_censored = output_path / "microdados_vacinacao.csv.gz"
    filename_uncensored = output_path / "microdados_vacinacao-uncensored.csv.gz"
    if not output_path.exists():
        output_path.mkdir(parents=True)

    with closing(requests.get(url, stream=True)) as response:
        writer_raw = CsvLazyDictWriter(filename_raw)
        raw_writerow = writer_raw.writerow
        writer_censored = CsvLazyDictWriter(filename_censored)
        censored_writerow = writer_censored.writerow
        writer_uncensored = CsvLazyDictWriter(filename_uncensored)
        uncensored_writerow = writer_uncensored.writerow

        file_size = response.headers.get("content-length")
        if file_size is not None:
            file_size = int(file_size)

        refresh_count = args.refresh_count
        fobj = (
            line.decode(args.input_encoding)
            for line in response.iter_lines(chunk_size=args.chunk_size)
        )
        reader = csv.DictReader(fobj, delimiter=";")
        progress = tqdm(reader, total=file_size, unit_scale=True, unit="B")
        for counter, row in enumerate(reader):
            raw_writerow(row)
            censored_writerow(convert_row_censored(row))
            uncensored_writerow(convert_row_uncensored(row))
            if counter % refresh_count == 0:
                progress.n = response.raw.tell()
                progress.refresh()
        progress.n = response.raw.tell()
        progress.close()
        writer_censored.close()
        writer_uncensored.close()


if __name__ == "__main__":
    main()
