#!/usr/bin/env bash

SRC_DIR="${1:-/Users/fred/Music/GOOD/2025-03}"
DST_DIR="${2:-/Users/fred/Music/NORMALIZED/2025-03}"

for i in "${SRC_DIR}"/*
do
    ./normalize_one_to_mp3.sh "$i" "$DST_DIR"
done
