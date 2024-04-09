import sys, re

GENRE_PATTERN = r"^.*Genre=\"(?:[A-Z])(?:-[A-Z])*(?:-\*([0-5]))\".*$"
STAR_PATTERN = r"Stars=\"([0-5])\""
VDJ_DB = "./database_tiny.xml"
VDJ_DB = "./database.xml"
OUTPUT = "./new.xml"

INPUT = sys.argv[1]
OUTPUT = sys.argv[2]

# line='  <Tags Author="Bicep" Title="Glue" Genre="C-H-R-*4" Album="Bicep" TrackNumber="2" Year="2017" Flag="1" />'
# line=   '  <Tags Author="Bicep" Title="Glue" Genre="C-H-R-*4" Album="Bicep" TrackNumber="2" Year="2017" Stars="5" Flag="1" />'
# line='C-H-R-*4'

def process_line(line: str) -> str:
    # print(line, end=None)
    m = re.search(GENRE_PATTERN, line)
    if m is None:
        return line
    score = m.group(1)

    # is there a "Stars=..." attribute?
    m = re.search(STAR_PATTERN, line)
    # print("39", m)
    if m:
        current_score = m.group(1)
        if current_score == score:
            return line
        return line[:m.start(0) + 7] + score + line[m.start(0) + 8:]
    else:
        return line[:-2] + f'Stars="{score}" />'
        

# print(process_line(line))


input_file = open(INPUT, 'r')
output_file = open(OUTPUT, 'w')
nb = 0
limit = 100000
while True:
    line = input_file.readline()
    if not line:
        break
    l = line.replace('\n','')
    processed_line = process_line(l)
    if processed_line != l:
        nb += 1
    if nb < limit:
        print(processed_line, file=output_file, end=None)
    else:
        print(l, file=output_file, end=None)

print(f"nb = {nb}", file=sys.stderr)
"""
cp ~/Library/Application\ Support/VirtualDJ/database.xml database.xml
"""