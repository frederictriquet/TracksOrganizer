#!/usr/bin/env bash

SRC_FILE="$1"
DST_DIR="$2"

FILENAME=$(basename "$SRC_FILE")
EXT=${FILENAME##*.}
OUT_FILE="${DST_DIR}/${FILENAME%.*}.mp3"
# echo ${OUT_FILE}
# echo $EXT

db=$(ffmpeg -i "$SRC_FILE" -vn -filter:a volumedetect -f null /dev/null 2>&1 | grep max_volume | cut -d: -f2 | cut -d' ' -f2)
# echo $(basename "$SRC_FILE") $db
if [ 1 -eq $(bc <<< "$db < 0.0") ]
then
    boost=$(bc <<< "- $db")
    db="${boost}dB"
    echo AMPLIFY $db
else
    echo KEEP AS IS
    db=''
fi

if [[ $db == '' && $EXT == 'mp3' ]]
then
    echo COPY
    [ -f "$OUT_FILE" ] || cp "$SRC_FILE" "$OUT_FILE"
elif [[ $db == '' ]]
then
    echo CONVERT ONLY
    ffmpeg -i "$SRC_FILE" -ab 320k -map_metadata 0 -id3v2_version 3 -write_id3v1 1 "${OUT_FILE}"
else
    echo BOOST
    ffmpeg -i "$SRC_FILE" -filter:a "volume=${db}" -ab 320k -map_metadata 0 -id3v2_version 3 -write_id3v1 1 "${OUT_FILE}"
fi
echo "------------------------------"