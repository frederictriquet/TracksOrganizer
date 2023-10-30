import mutagen
from mutagen.easyid3 import EasyID3  
import shutil
import glob
import os
import re

def glob_re(pattern, strings):
    return filter(re.compile(pattern).match, strings)


base_dir = '/Users/fred/Music/'
src_dir = f'{base_dir}4 GOODNAMES/'
# src_dir = f'{base_dir}GOOD/'
# filez = glob.glob(f'{src_dir}*.([Mm][Pp]3)|(flac)')
filez = glob_re(r'.*\.(mp3|Mp3|MP3|flac)', os.listdir(src_dir))
# filez = filez[0:1]
for file in filez:
  print(f'******************************** {file} ***')
  path = file.split('/')
  ext_length = 4
  if (path[-1][-5]=='.'): ext_length = 5
  filename = path[-1][:-ext_length].replace("\u200e","").replace(' – ', ' - ')
  print(f'filename = {filename}')
  f = filename.split(' - ')
  print(f'splitted = {f}')
  artist = f[0].strip() #.title()
  title = f[1].strip() #.title()
  fullpath = f'{src_dir}{file}'
  # try:
  #   tag = EasyID3(fullpath)
  # except:
  tag = mutagen.File(fullpath, easy=True)
  try:
    tag.add_tags()
  except:
    pass

  print(tag)
  tag['artist'] = artist
  tag['title'] = title
  tag['musicbrainz_artistid'] = 'unknown'
  print(tag)
  # print(f'artist="{artist}" ({tag["artist"][0]})')
  # print(f'title="{title}" ({mptagfile["title"][0]})')
  tag.save(fullpath)
  # tag.save(fullpath, v2_version=4)
  print(f'{artist} - {title}')