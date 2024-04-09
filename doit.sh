#!/usr/bin/env bash
D=$(date +%Y%m%d-%H%M)
DB=~/Library/Application\ Support/VirtualDJ/database.xml
CURRENTDB=database.xml-$D
cp "$DB" $CURRENTDB
python starify.py $CURRENTDB new.xml
unix2dos -f new.xml
cp new.xml ~/Library/Application\ Support/VirtualDJ/database.xml
