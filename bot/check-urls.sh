#!/bin/bash

set -e
SCRIPT_PATH=$(dirname $(readlink -f $0))

cd $SCRIPT_PATH
if [ -e "../.env" ]; then
	source ../.env
fi
mkdir -p data
OUTPUT_FILENAME="data/url-hash.csv"
rm -rf "$OUTPUT_FILENAME"
scrapy runspider url_spider.py --loglevel=INFO -a "output_filename=$OUTPUT_FILENAME"
s3cmd \
	--access_key="$S3_ACCESS_KEY" \
	--secret_key="$S3_SECRET_KEY" \
	--host="$S3_HOSTNAME" \
	--host-bucket="$S3_HOST_BUCKET" \
	put \
	$OUTPUT_FILENAME \
	s3://dataset/covid19/$(basename $OUTPUT_FILENAME)
