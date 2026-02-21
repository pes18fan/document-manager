#!/usr/bin/env bash
mkdir -p initial_small && ls *.tif | shuf -n 5 | xargs -I{} mv "{}" initial_small/
