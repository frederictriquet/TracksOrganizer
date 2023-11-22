
def milliseconds_to_string(ms: int) -> str:
    m = int(ms / 60000)
    s = int(ms / 1000) % 60
    return f'{m}:{s:02}'
