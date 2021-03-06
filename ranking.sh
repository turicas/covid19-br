#!/bin/bash

set -e

source .env
time echo "DROP TABLE IF EXISTS caso_full CASCADE;" | psql $PGURI
rows pgimport \
	--dialect=excel \
	--input-encoding=utf8 \
	--schema=schema/caso_full.csv \
	data/output/caso_full.csv.gz \
	$PGURI \
	caso_full
time cat sql/ranking-new-confirmed-and-deaths.sql | psql $PGURI
