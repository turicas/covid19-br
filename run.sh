#!/bin/bash

set -e
mkdir -p data/download data/output data/log

for table in caso boletim; do
	rm -rf data/output/${table}.csv*
	time scrapy runspider consolida.py \
		--loglevel=INFO \
		--logfile=data/log/${table}.log \
		-a input_filename=data/${table}_url.csv \
		-o data/output/${table}.csv
done
