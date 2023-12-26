import mutagen
import os

def dump(filename: str):
    print(f"{'*'*10}\n{filename}")
    file = mutagen.File(filename, easy=True)
    try:
        print(f'{int(file.info.bitrate/1000)} kb/s')
    except AttributeError:
        pass
    except ValueError:
        pass
    try:
        print(f'{file.info.sample_rate} Hz')
    except AttributeError:
        pass
    try:
        print(f'{file.info.length} seconds')
    except AttributeError:
        pass

    # print(file.tags['artist'])
path = './tracks/'
for f in map(lambda f: path+f, os.listdir(path)):
    dump(f)