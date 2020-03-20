#!/bin/bash

set -e

./run.sh

for table in caso boletim; do
	git add -f data/output/${table}.csv
	cp data/output/${table}.csv{,-bkp}
	gzip data/output/${table}.csv
	mv data/output/${table}.csv{-bkp,}
done
