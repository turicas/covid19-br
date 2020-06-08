#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

URL="https://covid-insumos.saude.gov.br/paineis/insumos/lista_csv_painel.php?output=csv"
DATETIME=$(date +%Y%m%d%H%M%S)

log "[insumos] Downloading last CSV for insumos ..."
wget -q -c -t 0 -O "$DOWNLOAD_PATH/insumos/insumos-${DATETIME}Z.csv" "$URL"

log "[insumos] Compressing last CSV for insumos ..."
gzip "$DOWNLOAD_PATH/insumos/insumos-${DATETIME}Z.csv"

#log "[insumos] Sending  CSV to Brasil.IO ..."
#TODO - para que isso funcione via GitHub Actions será necessário ter o HOST que brasil.io 
#       usa para o object storage S3, e definir as variáveis na configuração do GITHUB
# s3cmd \
# 	--access_key="$S3_ACCESS_KEY" \
# 	--secret_key="$S3_SECRET_KEY" \
# 	--host="$S3_HOSTNAME" \
# 	--host-bucket="$S3_HOST_BUCKET" \
# 	put \
# 	"$DOWNLOAD_PATH/insumos/insumos-${DATETIME}Z.csv.gz" \
# 	s3://dataset/$DATASET/insumos/insumos-${DATETIME}Z.csv.gz

log "[insumos] Done"
