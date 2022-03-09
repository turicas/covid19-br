# TODO: move this logic to spider format
import argparse
import logging
import os
import tempfile
from pathlib import Path

import requests
import rows
from tqdm import tqdm

from covid19br.parsers.rondonia import get_links, RondoniaParser


def download_file(url):
    if not url.startswith("http"):
        url = "https://" + url
    response = requests.get(url, headers={"User-Agent": "Mozilla"})
    return response.content


parser = argparse.ArgumentParser()
parser.add_argument("download_path")
parser.add_argument("output_path")
args = parser.parse_args()

download_path = Path(args.download_path)
output_path = Path(args.output_path)
for path in (download_path, output_path):
    if not path.exists():
        path.mkdir(parents=True)

bulletins = get_links()
for bulletin in tqdm(bulletins):
    date = bulletin["date"]

    if not date:
        # If bulletin date could not be parsed from HTML, save a temporary file
        # and use the PDF parser to do define it.
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(download_file(bulletin["url"]))
        temp.close()
        try:
            parser = RondoniaParser(temp.name)
        except RuntimeError:  # The file is not a PDF (probably HTML)
            logging.log(logging.ERROR, f"File is not PDF for bulletin: {bulletin}")
            continue
        date = parser.date
        pdf_filename = download_path / f"RO-{date}.pdf"
        os.rename(temp.name, pdf_filename)

    pdf_filename = download_path / f"RO-{date}.pdf"
    csv_filename = output_path / f"RO-{date}.csv"
    if not pdf_filename.exists():  # Download it
        with pdf_filename.open(mode="wb") as fobj:
            fobj.write(download_file(bulletin["url"]))

    try:
        parser = RondoniaParser(pdf_filename)
    except RuntimeError:
        logging.log(logging.ERROR, f"File is not a PDF ({bulletin})")
        continue
    try:
        data = list(parser.data)
    except RuntimeError:
        logging.log(logging.ERROR, f"File date is older than supported ({bulletin})")
        continue

    writer = rows.utils.CsvLazyDictWriter(csv_filename)
    for row in data:
        writer.writerow(row)
    writer.close()
