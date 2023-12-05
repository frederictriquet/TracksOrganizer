from pathlib import Path
import sys
from rename_one_from_tags import *

source_dir = Path(sys.argv[1])
dest_dir = Path(sys.argv[2])


extensions = ['.flac', '.aif', '.aiff', '.mp3']
tracks = [x for x in source_dir.iterdir() if x.suffix.lower() in extensions]

for track in tracks:
    move(track, dest_dir)