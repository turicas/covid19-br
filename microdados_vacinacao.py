import argparse
import csv
import logging
import sys
from functools import partial

from async_process_executor import pipeline
from rows.utils import CsvLazyDictWriter, open_compressed
from tqdm import tqdm

from covid19br.elasticsearch import ElasticSearch
from covid19br.vacinacao import convert_row_censored, convert_row_uncensored


def get_data_from_elasticsearch(api_url, index_name, sort_by, username, password, page_size):
    es = ElasticSearch(api_url)
    iterator = es.paginate(index=index_name, sort_by=sort_by, user=username, password=password, page_size=page_size)
    progress = tqdm(unit_scale=True)
    progress.desc = f"Downloading page 001"
    progress.refresh()
    for page_number, page in enumerate(iterator, start=1):
        progress.desc = f"Downloaded page {page_number:03d}"
        progress.refresh()
        yield page
    progress.close()


def get_data_from_csv(filename, page_size):
    with open_compressed(filename) as fobj:
        reader = csv.DictReader(fobj)
        iterator = rows.utils.ipartition(reader, page_size)
        for page in tqdm(iterator, unit_scale=True):
            yield page


def convert_rows(func, iterator):
    func = func if func is not None else lambda row: row
    for page in iterator:
        yield [func(row["_source"]) for row in page["hits"]["hits"]]


def write_csv(filename, iterator):
    writer = CsvLazyDictWriter(filename)
    for page in iterator:
        for row in page:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", default="ERROR")
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--no-censorship", action="store_true")
    parser.add_argument("--api-url", default="https://imunizacao-es.saude.gov.br/")
    parser.add_argument("--username", default="imunizacao_public")
    parser.add_argument("--password", default="qlto5t&7r_@+#Tlstigi")
    parser.add_argument("--index", default="desc-imunizacao")
    parser.add_argument("--ttl", default="10m")
    parser.add_argument("--page-size", default=10_000)
    parser.add_argument("--input-filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    pipeline.logger.addHandler(handler)
    pipeline.logger.setLevel(log_level)

    convert_row = convert_row_censored
    if args.raw:
        convert_row = None
    elif args.no_censorship:
        convert_row = convert_row_uncensored

    if args.input_filename:  # Use local CSV
        process_pipeline = [
            (
                get_data_from_csv,
                (args.input_filename, args.page_size),
            ),
            (
                partial(convert_rows, convert_row),
                tuple(),
            ),
            (
                write_csv,
                (args.output_filename,),
            ),
        ]

    else:  # Get data from ElasticSearch API
        process_pipeline = [
            (
                get_data_from_elasticsearch,
                (args.api_url, args.index, "@timestamp", args.username, args.password, args.page_size),
            ),
            (
                partial(convert_rows, convert_row),
                tuple(),
            ),
            (
                write_csv,
                (args.output_filename,),
            ),
        ]

    pipeline.execute(process_pipeline)


if __name__ == "__main__":
    main()
