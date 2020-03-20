#!/bin/bash

set -e
mkdir -p data/download data/output data/log

for spider in caso boletim; do
	time scrapy runspider consolida.py \
		--loglevel=INFO \
		--logfile=data/log/${spider}.log \
		-a input_filename=data/${spider}_url.csv \
		-o data/output/${spider}.csv
done
