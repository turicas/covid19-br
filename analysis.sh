#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

function create_database() {
	database_filename="$1"; shift
	clean="$1"

	rm -rf "$database_filename"
	for table in boletim caso obito_cartorio caso_full; do
		filename="data/output/${table}.csv.gz"
		if [ "$clean" = "--clean" ]; then
			rm -rf "$filename"
		fi
		if [ -e "$filename" ]; then
			echo "Using already downloaded $filename as $table"
		else
			echo "Downloading $table"
			url="https://data.brasil.io/dataset/covid19/${table}.csv.gz"
			rm -rf "$filename"
			wget -q -c -t 0 -O "$filename" "$url"
		fi
		rows csv2sqlite --schemas=schema/${table}.csv "$filename" "$database_filename"
	done
	for table in populacao-estimada-2019 epidemiological-week; do
		rows csv2sqlite --schemas=schema/${table}.csv data/${table}.csv $database_filename
	done
}

function execute_sql_file_no_output() {
	database=$1; shift
	filename=$1

	cat "$filename" | sqlite3 "$database"
}

function execute_sql_file_with_output() {
	database=$1; shift
	sql_filename=$1; shift
	output_filename=$1

	rows query \
		"$(cat $sql_filename)" \
		"$database" \
		--output="$output_filename"
}

function setup_database() {
	database=$1; shift

	for filename in sql/*setup.sql; do
		echo "Running setup $filename"
		execute_sql_file_no_output "$database" "$filename"
	done
}

function execute_sql_files() {
	database=$1; shift
	files=$@

	for filename in $files; do
		if [[ "$(basename $filename)" != *"setup.sql" ]]; then
			echo "Executing $filename and exporting data"
			output="data/analysis/$(basename $filename | sed 's/\.sql$/.csv.gz/')"
			execute_sql_file_with_output "$DATABASE" "$filename" "$output"
		fi
	done
}

DATABASE="$SCRIPT_PATH/data/covid19.sqlite"
mkdir -p "$SCRIPT_PATH/data/analysis" "$SCRIPT_PATH/data/output"
create_database "$DATABASE" "$1"
setup_database "$DATABASE"
execute_sql_files "$DATABASE" $SCRIPT_PATH/sql/*.sql
