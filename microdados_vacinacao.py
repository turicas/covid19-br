import argparse
import csv
import logging
import sys
from functools import partial

from async_process_executor import pipeline
from rows.utils import CsvLazyDictWriter, open_compressed
from tqdm import tqdm

from covid19br.elasticsearch import ElasticSearch
from covid19br.vacinacao import (
    convert_row_censored,
    convert_row_uncensored,
    get_field_converters,
)


RAW_KEYS = list(get_field_converters().keys())

def get_data_from_elasticsearch(
    api_url,
    username,
    password,
    index_name,
    query,
    sort_by,
    page_size,
    ttl,
):
    es = ElasticSearch(api_url, username=username, password=password)
    iterator = es.search(index_name, sort_by=sort_by, page_size=page_size, ttl=ttl, query=query)
    yield from tqdm(iterator, desc="Consuming ElasticSearch", unit_scale=True)


def get_data_from_csv(filename, page_size):
    with open_compressed(filename) as fobj:
        reader = csv.DictReader(fobj)
        iterator = rows.utils.ipartition(reader, page_size)
        for page in tqdm(iterator, unit_scale=True):
            yield page


def convert_row_raw(row):
    new = {key: row.pop(key, None) for key in RAW_KEYS}
    if row:
        raise ValueError(f"Unknown keys: {row.keys()}")
    return new

def convert_rows_page(func, iterator):
    func = func if func is not None else lambda row: row
    for page in iterator:
        yield [func(row) for row in page]


def convert_rows(func, iterator):
    for row in iterator:
        yield func(row)


def write_csv(filename, iterator):
    writer = CsvLazyDictWriter(filename)
    for row in iterator:
        writer.writerow(row)


def write_csv_page(filename, iterator):
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
    parser.add_argument("start_datetime")
    parser.add_argument("end_datetime")
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
        convert_row = convert_row_raw
    elif args.no_censorship:
        convert_row = convert_row_uncensored

    if args.input_filename:  # Use local CSV
        process_pipeline = [
            (
                get_data_from_csv,
                (args.input_filename, args.page_size),
            ),
            (
                partial(convert_rows_page, convert_row),
                tuple(),
            ),
            (
                write_csv_page,
                (args.output_filename,),
            ),
        ]

    else:  # Get data from ElasticSearch API
        timestamp_key = "vacina_dataAplicacao"
        query = {
            "range": {
                timestamp_key: {
                    "gte": args.start_datetime,
                    "lt": args.end_datetime,
                },
            },
        }
        if args.start_datetime == "None":
            del query["range"][timestamp_key]["gte"]

        process_pipeline = [
            (
                get_data_from_elasticsearch,
                (
                    args.api_url,
                    args.username,
                    args.password,
                    args.index,
                    query,
                    timestamp_key,
                    args.page_size,
                    args.ttl,
                ),
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
