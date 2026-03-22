#!/usr/bin/env bash
mkdir -p output && for f in *.png *.tif *.pdf *.jpg *.jpeg; do magick "$f" "output/$(basename "${f%.*}").jpg"; done
