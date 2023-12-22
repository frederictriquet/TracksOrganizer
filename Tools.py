from pathlib import Path
import re
from Logger import logger
def load_conf(yaml_filename: str):
    import yaml
    with open(yaml_filename) as file:
        stringdata = yaml.safe_load(file)
        return stringdata

def milliseconds_to_string(ms: int) -> str:
    m = int(ms / 60000)
    s = int(ms / 1000) % 60
    return f'{m}:{s:02}'

def bytes_to_mb(b):
    m = int(100 * b / 1024 / 1024) / 100
    return f'{m} Mb'

def genre_to_str(genre: str) -> str: # TODO put it in the conf ?
    genres = { 'A': 'A Cappella', 'C': 'Classic', 'D': 'Deep', 'F': 'Funny', 'G': 'Garden','H': 'House','L': 'Loop', 'P':'Power','R':'Retro','T':'Trance','U':'Unclassable','W':'Weed'}
    if genre not in genres:
        return ''
    return genres[genre]

def scan_paths(paths: list[Path], file_pattern: str) -> list[Path]:
    res = []
    r = re.compile(file_pattern, re.IGNORECASE)
    try:
        for p in paths:
            if p.is_file() and r.match(str(p)):
                res.append(p)
            elif p.is_dir():
                children = list(p.iterdir())
                res.extend(scan_paths(children, file_pattern))
    except PermissionError as e:
        logger.error(e)
    return res

if __name__ == '__main__':
    PATTERN = r'.*\.(mp3|flac|aif|aiff)'
    print(scan_paths([Path('../..')], PATTERN))
    # print(scan_paths([Path('tracks/01. GastoM, Aske Izan - Regreso.flac')], PATTERN))
