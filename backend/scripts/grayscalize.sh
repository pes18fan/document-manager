#!/usr/bin/env bash

set -e

INPUT_DIR="${1:-.}"
OUTPUT_DIR="$INPUT_DIR/grayscale"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Loop through tif/tiff files
for img in "$INPUT_DIR"/*.tif "$INPUT_DIR"/*.tiff; do
    [ -e "$img" ] || continue

    filename=$(basename "$img")
    out="$OUTPUT_DIR/$filename"

    echo "Converting $filename -> $out"

    magick "$img" -colorspace Gray "$out"
done

echo "Done. Grayscale images saved to: $OUTPUT_DIR"
