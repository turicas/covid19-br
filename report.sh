#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

log "Creating report..."
tempfile=$(mktemp)
time python report.py api | tee $tempfile
if [ ! -z "$ROCKETCHAT_USER_ID" ] && [ ! -z "$ROCKETCHAT_AUTH_TOKEN=" ]; then
	time python $SCRIPT_PATH/bot/rocketchat.py \
		--user_id $ROCKETCHAT_USER_ID \
		--auth_token $ROCKETCHAT_AUTH_TOKEN \
		"#covid19-anuncios" "$(cat $tempfile)"
fi
rm -rf $tempfile
