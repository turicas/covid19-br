#!/bin/bash

set -e
WORKDIR_PATH=$PWD
DATA_PATH="$WORKDIR_PATH/data/output"

source $WORKDIR_PATH/base.sh

for table in boletim caso caso_full obito_cartorio; do
    echo "Downloading $table"
    filename="${DATA_PATH}/${table}.csv.gz"
    url="https://data.brasil.io/dataset/covid19/${table}.csv.gz"
    rm -rf "$filename"
    wget -q -c -t 0 -O "$filename" "$url"
done

echo "Checando integridade dos arquivos..."
cd $DATA_PATH
rm -f SHA512SUMS
wget -q -c -t 0 -O SHA512SUMS "https://data.brasil.io/dataset/covid19/SHA512SUMS"
sha512sum -c SHA512SUMS

echo "Extraindo arquivos..."
gunzip -fk *.gz

echo "Validando arquivos..."
cd $WORKDIR_PATH
goodtables datapackage.json
