#!/bin/bash

set -eu -o pipefail

rm -v DerivedArtwork/*

py -3 cardbuilder.py

id=$(cat manifest.json | jq -r '.name + "_" + .version_number' | tr -d '\r')

cat HS_cards.csv | yq -p=csv -r '. | map(select(."!artsource")) | map("- " + .displayedName + ": " + ."!artsource") | join("\n")' -o=y > credits.md

rm -v "${id}.zip" || :

zip "${id}.zip" \
  icon.png \
  README.md \
  manifest.json \
  *.jlpk \
  *.jldr2 \
  readmeassets/* \
  Artwork/*.png \
  Cards/*.jldr2 \
  DerivedArtwork/*.png