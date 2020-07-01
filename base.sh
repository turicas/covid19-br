#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
DOWNLOAD_PATH="$SCRIPT_PATH/data/download"
LOG_PATH="$SCRIPT_PATH/data/log"
OUTPUT_PATH="$SCRIPT_PATH/data/output"
ERROR_PATH="$SCRIPT_PATH/data/error"
DATASET="covid19"

function log() {
	echo "[$(date +"%Y-%m-%d %H:%M:%S")] $@"
}

function sort_csv() {
	filename=$1

	tempfile=$(mktemp)
	head -1 "$filename" > $tempfile
	tail +2 "$filename" | sort >> "$tempfile"
	mv "$tempfile" "$filename"
}
