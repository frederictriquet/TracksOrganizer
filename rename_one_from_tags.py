import shutil
import sys, os
import vlc
from pathlib import Path

instance = vlc.get_default_instance()
mediaplayer = instance.media_player_new()
# print('Artist:     ',media.get_meta(vlc.Meta.Artist))
# print('Title:      ', media.get_meta(vlc.Meta.Title))
# print('Description:', media.get_meta(vlc.Meta.Description))
# print('Genre:      ', media.get_meta(vlc.Meta.Genre))
def retrieve_info(filename: Path):
    media = instance.media_new(filename)
    media.parse()
    ext = filename.suffix
    artist = media.get_meta(vlc.Meta.Artist)
    title = media.get_meta(vlc.Meta.Title)
    return (artist, title, ext)


def get_new_name(filename: Path):
    artist, title, ext = retrieve_info(filename)
    return f'{artist} - {title}{ext}'


def checks(source_file: Path, dest_dir: Path):
    if not source_file.exists():
        raise Exception('source_file does not exist')
    if not source_file.is_file():
        raise Exception('source_file is not a file')
    if not dest_dir.exists():
        raise Exception('dest_dir does not exist')
    if not dest_dir.is_dir():
        raise Exception('dest_dir is not a directory')


def move(source_file: Path, dest_dir: Path):
    print(source_file)
    checks(source_file, dest_dir)
    new_name = get_new_name(source_file)
    new_dest = dest_dir / new_name
    if new_dest.exists():
        raise Exception('new_dest exists')
    print('--> ', new_dest)
    created = shutil.move(source_file, new_dest)
    if not created:
        raise Exception('not created')



if __name__ == '__main__':
    source_file = Path(sys.argv[1])
    dest_dir = Path(sys.argv[2])
    move(source_file, dest_dir)

