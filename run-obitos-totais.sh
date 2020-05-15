#!/bin/bash

set -e
SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh

OUTPUT_FILENAME="$DOWNLOAD_PATH/obitos_totais.csv"
FINAL_FILENAME="$OUTPUT_PATH/obito_totais.csv.gz"
rm -rf "$OUTPUT_FILENAME" "$FINAL_FILENAME"
mkdir -p "$DOWNLOAD_PATH" "$OUTPUT_PATH" "$LOG_PATH"
time scrapy runspider obitos_totais_spider.py \
	-s HTTPCACHE_ENABLED=True \
	-s HTTPCACHE_ALWAYS_STORE=True \
	--loglevel=INFO \
	--logfile="$LOG_PATH/obitos_totais.log" \
	-o "$OUTPUT_FILENAME"
