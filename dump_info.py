import mutagen
import os

def dump(filename: str):
    print(f"{'*'*10}\n{filename}")
    file = mutagen.File(filename, easy=True)
    try:
        print(f'{int(file.info.bitrate/1000)} kb/s')
    except:
        pass
    try:
        print(f'{file.info.sample_rate} Hz')
    except:
        pass
    try:
        print(f'{file.info.length} seconds')
    except:
        pass

    # print(file.tags['artist'])
path = './tracks/'
for f in map(lambda f: path+f, os.listdir(path)):
    dump(f)