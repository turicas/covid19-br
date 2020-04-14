#!/bin/bash

#Cores
RED='\033[0;31m'
LIGHT_GREEN='\033[0;32m'
YBLUE='\033[1;33;1;44m'
NC='\033[0m' # No Color

set -e
if [[ $OSTYPE == "darwin"* ]]; then
  SCRIPT_PATH=$(dirname $(pwd)/$(basename $0))
else
  SCRIPT_PATH=$(dirname $(readlink -f $0))
fi

echo -e "${LIGHT_GREEN}\n Coletando dados Brasil \n${NC}"

source $SCRIPT_PATH/base.sh

mkdir -p $DOWNLOAD_PATH $OUTPUT_PATH $LOG_PATH
for state in ce pr rr sp; do
	echo -e "${YBLUE} Estado: ${state} ${NC}"
	log_filename="$LOG_PATH/caso-${state}.log"
	csv_filename="$OUTPUT_PATH/caso-${state}.csv"
	rm -rf "$log_filename" "$csv_filename"
	time scrapy runspider \
		--loglevel=INFO \
		--logfile="$log_filename" \
		-o "$csv_filename" \
		corona_${state}_spider.py	
done
