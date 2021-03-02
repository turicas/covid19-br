import argparse
import csv
from functools import partial

from rows.utils import CsvLazyDictWriter, open_compressed
from tqdm import tqdm

from covid19br.elasticsearch import ElasticSearchConsumer
from covid19br.vacinacao import convert_row_censored, convert_row_uncensored


def convert_rows(func, page):
    return [func(row["_source"]) for row in page["hits"]["hits"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--no-censorship", action="store_true")
    parser.add_argument("--username", default="imunizacao_public")
    parser.add_argument("--password", default="qlto5t&7r_@+#Tlstigi")
    parser.add_argument("--api-url", default="https://imunizacao-es.saude.gov.br/")
    parser.add_argument("--index", default="desc-imunizacao")
    parser.add_argument("--ttl", default="10m")
    parser.add_argument("--input-filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    convert_row = convert_row_censored
    if args.raw:
        convert_row = lambda row: row
    elif args.no_censorship:
        convert_row = convert_row_uncensored

    if args.input_filename:  # Use local CSV
        writer = CsvLazyDictWriter(args.output_filename)
        with open_compressed(args.input_filename) as in_fobj:
            reader = csv.DictReader(in_fobj)
            for row in tqdm(reader, unit_scale=True):
                writer.writerow(convert_row(row))
        writer.close()

    else:  # Get data from ElasticSearch API

        ElasticSearchConsumer(
            api_url=args.api_url,
            index_name=args.index,
            sort_by="@timestamp",
            username=args.username,
            password=args.password,
            convert_function=partial(convert_rows, convert_row),
            output_filename=args.output_filename,
        ).run()


if __name__ == "__main__":
    main()
