import argparse
import os
import re
import sys
from pathlib import Path

from rows.utils import pgexport
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("sql_filename")
    parser.add_argument("output_path")
    args = parser.parse_args()

    if args.database_url is None:
        print("ERROR: you must specify --database-url or set DATABASE_URL environment variable.", file=sys.stderr)
        exit(1)
    elif not Path(args.sql_filename).absolute().exists():
        print(f"ERROR: file {repr(args.sql_filename)} not found")
        exit(2)

    output_path = Path(args.output_path).absolute()
    if not output_path.exists():
        output_path.mkdir(parents=True)
    with open(args.sql_filename) as fobj:
        query_data = fobj.read()

    result = re.split("^-- filename: (.*)$", query_data, flags=re.MULTILINE)
    queries = {}
    for output_filename, query in zip(result[1::2], result[2::2]):
        query = query.strip()
        if query.endswith(";"):
            query = query[:-1].strip()
        queries[output_path / output_filename] = query

    for output_filename, query in tqdm(queries.items()):
        pgexport(
            database_uri=args.database_url,
            table_name_or_query=query,
            filename=output_filename,
            is_query=True,
        )


if __name__ == "__main__":
    main()
