#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

boletim_filename="$OUTPUT_PATH/boletim.csv.gz"
caso_filename="$OUTPUT_PATH/caso.csv.gz"
full_filename="$OUTPUT_PATH/caso_full.csv.gz"
rm -rf "$boletim_filename" "$caso_filename" "$full_filename" "$ERROR_PATH"
mkdir -p "$OUTPUT_PATH" "$LOG_PATH" "$ERROR_PATH"

time scrapy runspider consolida.py \
	--loglevel="INFO" \
	--logfile="$LOG_PATH/consolida.log" \
	-a boletim_filename="$boletim_filename" \
	-a caso_filename="$caso_filename"
if [ $(ls $ERROR_PATH/errors-*.csv 2>/dev/null | wc -l) -gt 0 ]; then
	# Some error happened
	exit 255
fi
time python full.py "$caso_filename" "$full_filename"
