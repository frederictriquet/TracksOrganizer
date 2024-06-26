#!/usr/bin/env bash

SRC_DIR="$1"
DST_DIR="$2"

for i in "${SRC_DIR}"/*
do
    ./normalize_one_to_mp3.sh "$i" "$DST_DIR"
done
