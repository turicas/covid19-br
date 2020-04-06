#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -f $0))
source $SCRIPT_PATH/base.sh

caso_filename="$OUTPUT_PATH/caso.csv.gz"
boletim_filename="$OUTPUT_PATH/boletim.csv.gz"

gunzip -fk ./data/output/*.gz
goodtables datapackage.json

