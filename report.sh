#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

log "Creating report..."
tempfile=$(mktemp)
time python report.py local | tee $tempfile
if [ ! -z "$ROCKETCHAT_USERNAME" ] && [ ! -z "$ROCKETCHAT_PASSWORD" ]; then
	time python $SCRIPT_PATH/bot/rocketchat.py \
		--username $ROCKETCHAT_USERNAME \
		--password $ROCKETCHAT_PASSWORD \
		"#covid19-anuncios" "$(cat $tempfile)"
fi
rm -rf $tempfile
