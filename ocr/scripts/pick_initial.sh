#!/usr/bin/env bash
INPUT_DIR="${1:-.}"
OUTPUT_DIR="$INPUT_DIR/initial_small"

mkdir -p "$OUTPUT_DIR" && ls "$INPUT_DIR"/*.tif | shuf -n 5 | xargs -I{} mv "{}" "$OUTPUT_DIR"
