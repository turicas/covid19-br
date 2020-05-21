#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

OUTPUT_FILENAME="$DOWNLOAD_PATH/obitos_totais.csv"
FINAL_FILENAME="$OUTPUT_PATH/obito_totais.csv.gz"
rm -rf "$OUTPUT_FILENAME" "$FINAL_FILENAME"
mkdir -p "$DOWNLOAD_PATH" "$OUTPUT_PATH" "$LOG_PATH"
time scrapy runspider obitos_totais_spider.py \
	-s HTTPCACHE_ENABLED=True \
	-s HTTPCACHE_ALWAYS_STORE=True \
	-s HTTPCACHE_IGNORE_HTTP_CODES=500,504 \
	-s AUTOTHROTTLE_ENABLED=True \
	-s RETRY_TIMES=4 \
	--loglevel=INFO \
	--logfile="$LOG_PATH/obitos_totais.log" \
	-o "$OUTPUT_FILENAME"
