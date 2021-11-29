#!/bin/bash

set -e

output_path="boletim"
today="$(date +'%Y-%m-%d')"
remote_filename="dataset/covid19/boletim/${today}.png"
local_filename="$output_path/${today}.png"
image_url="https://data.brasil.io/$remote_filename"
mkdir -p $output_path

# Take dashboard screenshot
docker-compose run worker python /app/screenshot.py /app/$local_filename

# Upload file and create DailyBulletin entry
s3cmd put $local_filename s3://$remote_filename
ssh ${BRASILIO_SSH_USER}@${BRASILIO_SSH_SERVER} \
	"dokku run brasilio-web python manage.py update_bulletin $today $image_url"
