#!/bin/bash

set -e
mkdir -p data/download data/output data/log

for state in pr; do
	log_filename="data/log/caso-${state}.log"
	csv_filename="data/output/caso-${state}.csv"
	rm -rf "$log_filename" "$csv_filename"
	time scrapy runspider \
		--loglevel=INFO \
		--logfile="$log_filename" \
		-o "$csv_filename" \
		corona_${state}_spider.py
done
