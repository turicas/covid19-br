#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

function upload_table_file() {
	table=$1

	log "[$table] Copying data to static file server"
	s3cmd put data/output/${table}.csv.gz s3://dataset/$DATASET/${table}.csv.gz
}

function update_table() {
	table=$1

	log "[$table] Executing update command"
	ssh $BRASILIO_SSH_USER@$BRASILIO_SSH_SERVER "$BRASILIO_UPDATE_COMMAND $DATASET $table"
}

log "Cleaning data path and collecting data"
./run-obitos.sh
./run-obitos-totais.sh
./run.sh

source $SCRIPT_PATH/.env
for table in boletim caso caso_full obito_cartorio; do
	upload_table_file $table
	update_table $table
done

log "Generating file list page"
python create_html.py dataset $DATASET $(date +"%Y-%m-%d") $SCRIPT_PATH/data/output/
s3cmd put data/output/SHA512SUMS s3://dataset/$DATASET/SHA512SUMS
s3cmd put data/output/_meta/list.html s3://dataset/$DATASET/_meta/list.html

./report.sh
