#!/bin/bash

set -e
SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh

mkdir -p $OUTPUT_PATH $LOG_PATH
caso_filename="$OUTPUT_PATH/caso.csv.gz"
boletim_filename="$OUTPUT_PATH/boletim.csv.gz"
rm -rf "$boletim_filename" "$caso_filename"
time scrapy runspider consolida.py \
	--loglevel=INFO \
	--logfile=$LOG_PATH/consolida.log \
	-a boletim_filename=$boletim_filename \
	-a caso_filename=$caso_filename
#sort_csv $output_filename
