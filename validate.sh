#!/bin/bash

set -e
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
source $SCRIPT_PATH/base.sh

for table in boletim caso caso_full obito_cartorio; do
    echo "Downloading $table"
    filename="${SCRIPT_PATH}/data/output/${table}.csv.gz"
    url="https://data.brasil.io/dataset/covid19/${table}.csv.gz"
    rm -rf "$filename"
    wget -q -c -t 0 -O "$filename" "$url"
done

echo "Checando integridade dos arquivos..."
cd "$SCRIPT_PATH/data/output"
rm -f "SHA512SUMS"
wget -q -c -t 0 -O "SHA512SUMS" "https://data.brasil.io/dataset/covid19/SHA512SUMS"
sha512sum -c SHA512SUMS

cd $SCRIPT_PATH
gunzip -fk $SCRIPT_PATH/data/output/*.gz
goodtables datapackage.json
