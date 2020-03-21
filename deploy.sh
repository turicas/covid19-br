#!/bin/bash

set -e
SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh

log "Cleaning data path and collecting data"
rm -rf $OUTPUT_PATH/*.csv.gz
./run.sh

log "Preparing data to be commited and sent to Brasil.IO server"
old_path="$(pwd)"
cd $OUTPUT_PATH
for table in caso boletim; do
	git add -f ${table}.csv
	cp ${table}.csv{,-bkp}
	gzip ${table}.csv
	mv ${table}.csv{-bkp,}
done
cd "$old_path"

log "Copying data to server"
source $SCRIPT_PATH/.env
scp $OUTPUT_PATH/*.csv.gz $BRASILIO_SSH_USER@$BRASILIO_SSH_SERVER:$BRASILIO_DATA_PATH/covid19/

log "Executing update command"
ssh $BRASILIO_SSH_USER@$BRASILIO_SSH_SERVER "$BRASILIO_UPDATE_COMMAND"

log "Done! Now you can git commit and push :)"
