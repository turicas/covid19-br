#!/bin/bash

set -e

function create_database() {
	database_filename="$1"; shift
	clean="$1"

	rm -rf "$database_filename"
	for table in boletim caso obito_cartorio caso_full; do
		filename="data/${table}.csv"
		if [ "$clean" = "--clean" ] && [ "$table" != "populacao-estimada-2019" ]; then
			rm -rf "$filename" "${filename}.gz"
		fi
		if [ -e "$filename" ]; then
			echo "Using already downloaded $filename as $table"
		elif [ -e "${filename}.gz" ]; then
			filename="${filename}.gz"
			echo "Using already downloaded $filename as $table"
		else
			filename="${filename}.gz"
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

DATABASE="data/covid19.sqlite"
mkdir -p data/analysis
create_database $DATABASE "$1"
setup_database $DATABASE
execute_sql_files $DATABASE sql/*.sql
