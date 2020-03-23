#!/bin/bash

set -e
SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh
DATASET="covid19"

log "Cleaning data path and collecting data"
rm -rf $OUTPUT_PATH/*.csv.gz
./run.sh

source $SCRIPT_PATH/.env
for table in boletim caso; do
	log "[$table] Copying data to static file server"
	s3cmd put data/output/${table}.csv.gz s3://dataset/$DATASET/${table}.csv.gz

	log "[$table] Executing update command"
	ssh $BRASILIO_SSH_USER@$BRASILIO_SSH_SERVER "$BRASILIO_UPDATE_COMMAND $DATASET $table"
done

log "Done! Enjoy your data :)"
