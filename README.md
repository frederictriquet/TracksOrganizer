Python application using PyQt6 that helps organize your tracks (mp3, flac, aiff).

```
python organizer.py conf.yml
sudo apt install qt6-base-dev
sudo apt-get install -qq libglu1-mesa-dev libx11-xcb-dev ^libxcb*
```


ffmpeg -i out.mp3 -ac 1 -filter:a aresample=8000 -map 0:a -c:a pcm_s16le -f data - | \
    gnuplot -p -e "plot '<cat' binary filetype=bin format='%int16' endian=little array=1:0 with lines;"

ffmpeg -i out.mp3 -ac 1 -filter:a aresample=80 -map 0:a -c:a pcm_s16le -f data - | \
    gnuplot -p -e "plot '<cat' binary filetype=bin format='%int16' endian=little array=1:0 with lines;"

ffmpeg -i out.mp3 -ac 1 -filter:a aresample=80 -map 0:a -c:a pcm_s16le -f data - | hexdump

ffmpeg -formats | grep PCM

ffmpeg -i out.mp3 -ac 1 -filter:a aresample=80 -map 0:a -c:a pcm_u8 -f data - | hexdump

ffmpeg -i out.mp3 -ac 1 -filter:a aresample=80 -map 0:a -c:a pcm_s8 -f data - |  \
    gnuplot -p -e "plot '<cat' binary filetype=bin format='%int8' array=1:0 with lines;"


mode 4 canaux
R, G, B, W

mode 8 canaux
dimmer, R, G, B, W, Strobe (slow -> fast)
7 -> jump
    0-3 noir
    4-19 rouge
    20-35 vert
    36-51 bleu
    52-67 blanc
    68-83 jaune
    84-99 autre jaune
    110-127 blanc
    128-169 jump
    170-210 fade
    211-255 rien
8 -> speed (jump)


yt-dlp -f "bestaudio/best" -ciw -o "%(title)s.%(ext)s" -v --extract-audio --audio-quality 0 --audio-format mp3
https://www.youtube.com/watch?v=BcK8zq5Ttlg