
def milliseconds_to_string(ms: int) -> str:
    m = int(ms / 60000)
    s = int(ms / 1000) % 60
    return f'{m}:{s:02}'

def bytes_to_Mb(b):
    m = int(100 * b / 1024 / 1024) / 100
    return f'{m} Mb'
