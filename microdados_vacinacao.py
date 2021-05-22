import argparse
import csv
import re
import shlex
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from urllib.request import urlopen

import requests
from lxml.html import document_fromstring
from rows.utils import CsvLazyDictWriter, open_compressed
from tqdm import tqdm

from covid19br.vacinacao import convert_row_uncensored, censor


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


def download_file_aria2c(url, filename, connections=4):
    command = f"""
        aria2c \
            --dir "{filename.parent.absolute()}" \
            -s "{connections}" \
            -x "{connections}" \
            -o "{filename.name}" \
            "{url}"
    """.strip()
    subprocess.run(shlex.split(command))


def download_file_curl(url, filename):
    with open(output_filename, mode="wb") as fobj:
        p1 = subprocess.Popen(
            shlex.split(f'curl "{url}"'),
            stdout=subprocess.PIPE,
            stderr=sys.stdout,
        )
        p2 = subprocess.Popen(
            shlex.split("xz -0 -"),
            stdin=p1.stdout,
            stdout=fobj,
        )
        stdout, stderr = p2.communicate()
        p2.wait()
        p1.wait()
    return stdout, stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=1_024 * 1_024)
    parser.add_argument("--refresh-count", type=int, default=10_000)
    parser.add_argument("--input-encoding", type=str, default="utf-8")
    parser.add_argument("--connections", type=int, default=8)
    parser.add_argument("--preserve-raw", action="store_true")
    parser.add_argument("--buffering", type=int, default=8 * 1024 * 1024)
    args = parser.parse_args()

    # TODO: adicionar opção para selecionar qual dos 3 possíveis CSVs o script
    # irá gerar.
    # TODO: configurar saída do logger para arquivo e não stdout/stderr
    # TODO: adicionar opção para salvar ou não CSV original (compactado)

    url, date = get_latest_url_and_date()
    output_path = Path(__file__).parent / "data" / "output"
    filename_raw = output_path / f"microdados_vacinacao-raw-{date}.csv.xz"
    filename_censored = output_path / "microdados_vacinacao.csv.gz"
    filename_uncensored = output_path / "microdados_vacinacao-uncensored.csv.gz"
    if not output_path.exists():
        output_path.mkdir(parents=True)

    download_file_curl(url, filename_raw)

    with open_compressed(filename_raw) as fobj:
        fobj_censored = open_compressed(filename_censored, mode="w", buffering=args.buffering)
        writer_censored = CsvLazyDictWriter(fobj_censored)
        censored_writerow = writer_censored.writerow

        fobj_uncensored = open_compressed(filename_uncensored, mode="w", buffering=args.buffering)
        writer_uncensored = CsvLazyDictWriter(fobj_uncensored)
        uncensored_writerow = writer_uncensored.writerow

        refresh_count = args.refresh_count
        reader = csv.DictReader(fobj, delimiter=";")
        for counter, row in tqdm(enumerate(reader), unit_scale=True, unit="row"):
            row = convert_row_uncensored(row)
            uncensored_writerow(row)
            censor(row)
            censored_writerow(row)
        writer_censored.close()
        writer_uncensored.close()

    if not args.preserve_raw:
        filename_raw.unlink()


if __name__ == "__main__":
    main()
