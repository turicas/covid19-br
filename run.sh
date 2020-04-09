#!/bin/bash

set -e
SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh

rm -rf $OUTPUT_PATH/*.csv.gz $ERROR_PATH
mkdir -p "$OUTPUT_PATH" "$LOG_PATH" "$ERROR_PATH"
caso_filename="$OUTPUT_PATH/caso.csv.gz"
boletim_filename="$OUTPUT_PATH/boletim.csv.gz"

time scrapy runspider consolida.py \
	--loglevel="INFO" \
	--logfile="$LOG_PATH/consolida.log" \
	-a boletim_filename="$boletim_filename" \
	-a caso_filename="$caso_filename"
if [ $(ls $ERROR_PATH/errors-*.csv 2>/dev/null | wc -l) -gt 0 ]; then
	# Some error happened
	exit 255
fi

# Deaths from notary's offices
OUTPUT_FILENAME="$DOWNLOAD_PATH/obitos.csv"
FINAL_FILENAME="$OUTPUT_PATH/obito-cartorio.csv.gz"
rm -rf "$OUTPUT_FILENAME" "$FINAL_FILENAME"
mkdir -p $(dirname "$OUTPUT_FILENAME") $(dirname "$FINAL_FILENAME")
time scrapy runspider obitos_spider.py \
	-s HTTPCACHE_ENABLED=True \
	--loglevel=INFO \
	--logfile="$LOG_PATH/obitos.log" \
	-o "$OUTPUT_FILENAME"
time python obitos_convert.py "$OUTPUT_FILENAME" "$FINAL_FILENAME"
rm "$OUTPUT_FILENAME"
