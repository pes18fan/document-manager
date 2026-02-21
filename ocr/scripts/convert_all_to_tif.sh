#!/usr/bin/env bash
mkdir -p output && for f in *.jpg *.jpeg; do magick "$f" "output/$(basename "${f%.*}").tif"; done
