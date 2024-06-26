#!/usr/bin/env bash
WHERE=/Users/fred/Music/GOOD/2024-06
WHERE=/Users/fred/Music/GOOD/PROCESSED
WHERE=/Users/fred/Music/GOOD/RECENT
WHERE=$1
for i in $WHERE/*
do
    db=$(ffmpeg -i "$i" -vn -filter:a volumedetect -f null /dev/null 2>&1 | grep max_volume | cut -d: -f2 | cut -d' ' -f2)
    echo "$i;$db"
    # echo "$i;$db" >> volumes.csv
done
