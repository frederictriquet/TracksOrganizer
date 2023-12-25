from pathlib import Path
import re
from Logger import logger


def milliseconds_to_string(ms: int) -> str:
    m = int(ms / 60000)
    s = int(ms / 1000) % 60
    return f'{m}:{s:02}'

def bytes_to_mb(b):
    m = int(100 * b / 1024 / 1024) / 100
    return f'{m} Mb'

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
