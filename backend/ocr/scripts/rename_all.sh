#!/usr/bin/env bash
OUT="output"
mkdir -p "$OUT" || true
i=1
for f in *.jpg
do 
    [ -e "$img" ] || continue

    printf -v n "%02d" "$i"
    mv "$f" "$OUT/image-$n.jpg"
    ((i++))
done
