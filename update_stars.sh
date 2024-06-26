#!/usr/bin/env bash

sqlite3 "/Users/fred/Music/Engine Library/Database2/m.db" "update track set rating=cast(substr(genre,-1) as integer)*20"