#!/bin/bash

set -e
SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh

mkdir -p $OUTPUT_PATH $LOG_PATH
for table in caso boletim; do
	output_filename="$OUTPUT_PATH/${table}.csv"
	rm -rf "$output_filename" "${output_filename}.gz"
	time scrapy runspider consolida.py \
		--loglevel=INFO \
		--logfile=$LOG_PATH/${table}.log \
		-a input_filename=data/${table}_url.csv \
		-o "$output_filename"
	sort_csv $output_filename
done
