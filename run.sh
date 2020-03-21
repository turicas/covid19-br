#!/bin/bash

function sort_csv() {
	filename=$1

	tempfile=$(mktemp)
	head -1 "$filename" > $tempfile
	tail +2 "$filename" | sort >> "$tempfile"
	mv "$tempfile" "$filename"
}

set -e
mkdir -p data/download data/output data/log

for table in caso boletim; do
	output_filename="data/output/${table}.csv"
	rm -rf "$output_filename" "${output_filename}.gz"
	time scrapy runspider consolida.py \
		--loglevel=INFO \
		--logfile=data/log/${table}.log \
		-a input_filename=data/${table}_url.csv \
		-o "$output_filename"
	sort_csv $output_filename
done
