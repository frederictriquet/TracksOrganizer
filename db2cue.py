import sqlite3, datetime

con = sqlite3.connect("Database2/m.db")
cur = con.cursor()

start_time = int(datetime.datetime(2024, 12, 22, 16, 14, 30, 0).timestamp())

req = f"""
select artist, title , datetime(timeLastPlayed, 'unixepoch', 'localtime'), timeLastPlayed-{start_time} as diff  from Track t 
where isPlayed
and diff >= 0
ORDER by timeLastPlayed  limit 200
"""

mp3filename = "Winter Weedmix'24"


res = cur.execute(req)
with open(f'{mp3filename}.cue','w') as cue:
    cue.write('PERFORMER "DJ Frezz"\n')
    cue.write(f'FILE "{mp3filename}.mp3" MP3\n')
    i = 1
    for r in res.fetchall():
        print(r)
        cue.write(f'  TRACK {i:02d} AUDIO\n')
        cue.write(f'    TITLE "{r[1]}"\n')
        cue.write(f'    PERFORMER "{r[0]}"\n')
        m = int(r[3] / 60)
        s = r[3] % 60
        cue.write(f'    INDEX 01 {m:02d}:{s:02d}:00\n')
        i+=1