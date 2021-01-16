#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

DEPLOY_TYPE="$1"

if [[ -z "$DEPLOY_TYPE" ]] || [[ "$DEPLOY_TYPE" != "simple"  && "$DEPLOY_TYPE" != "simple-report"  && "$DEPLOY_TYPE" != "full" ]]; then
	echo "ERROR - Usage: $0 <simple|full>"
	exit 1
fi

if [ "$DEPLOY_TYPE" = "simple" ]; then
	COMPLETE=0
	REPORT=0
elif [ "$DEPLOY_TYPE" = "simple-report" ]; then
	COMPLETE=0
	REPORT=1
elif [ "$DEPLOY_TYPE" = "full" ]; then
	COMPLETE=1
	REPORT=1
fi

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

function update_dataset_list() {
	dataset=$1

	log "[$dataset] Executing update file list"
	ssh $BRASILIO_SSH_USER@$BRASILIO_SSH_SERVER "$BRASILIO_UPDATE_FILE_LIST_COMMAND $DATASET"
}

log "Cleaning data path and collecting data"
if [ "$COMPLETE" = "1" ]; then
	./run-obitos.sh
fi
./run.sh

source $SCRIPT_PATH/.env
if [ "$COMPLETE" = "1" ]; then
	for table in boletim caso caso_full obito_cartorio; do
		upload_table_file $table
		update_table $table
	done
else
	for table in boletim caso caso_full; do
		upload_table_file $table
		update_table $table
	done
fi

update_dataset_list "covid19"

if [ "$REPORT" = "1" ]; then
	./report.sh
fi

time python ocupacao.py
