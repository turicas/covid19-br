#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh

for table in boletim caso caso_full obito_cartorio; do
    echo "Downloading $table"
    filename="${SCRIPT_PATH}/data/output/${table}.csv.gz"
    url="https://data.brasil.io/dataset/covid19/${table}.csv.gz"
    rm -rf "$filename"
    wget -q -c -t 0 -O "$filename" "$url"
done

rm -f ${SCRIPT_PATH}/data/output/SHA512SUMS
wget -q -c -t 0 -O ${SCRIPT_PATH}/data/output/SHA512SUMS "https://data.brasil.io/dataset/covid19/SHA512SUMS"

cd ${SCRIPT_PATH}/data/output

echo "Checando integridade dos arquivos..."
sha512sum -c SHA512SUMS
if [ $? != 0 ]; then
    exit 1
fi

cd $SCRIPT_PATH

gunzip -fk $SCRIPT_PATH/data/output/*.gz
goodtables datapackage.json