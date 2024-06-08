#!/usr/bin/env bash
rm -f out.mp4 out.mp3 out.txt
AUDIO="$1"
START=$2
STYLE=$3
VIDEO="~/Movies/CapCut/template_insta.mp4"
TEMPLATE=./Templates/$STYLE.mp4
FILENAME=$(basename -- "$AUDIO")
BASENAME="${FILENAME%.*}"
echo $BASENAME > out.txt

ffmpeg -i "$AUDIO" \
    -ss $START -t 00:00:30 \
    out.mp3
ffmpeg -an -i $TEMPLATE \
    -vn -i out.mp3 \
    -vf "fade=t=in:st=0:d=2,fade=t=out:st=28:d=2,drawtext=textfile=out.txt:fontfile=foo.ttf:y=40:x=w-(t-2.5)*w/3.5:fontcolor=white:fontsize=150:shadowx=2:shadowy=2" \
    -af "afade=t=in:st=0:d=2,afade=t=out:st=28:d=2" \
    out.mp4

mv out.mp4 ~/Movies/Insta/"$BASENAME".mp4
    # -vf "drawtext=text='StackOverflow':fontfile=/path/to/font.ttf:fontsize=30:fontcolor=white:x=100:y=100" \
    # -c:v copy \


# ffmpeg -an -i ~/Movies/CapCut/template.mp4 \
#     -vn -i ~/Music/GOOD/RECENT/Undercatt\ -\ Vegas\ \(Original\ Mix\).flac \
#     -c:v copy \
#     -filter_complex "[1]atrim=start=30:end=60" \
#     out.mp4

#    -af "afade=t=in:st=0:d=2,afade=t=out:st=28:d=2" \
#    -map "[0:v]" -map "[1:a]" \

# https://stackoverflow.com/questions/17623676/text-on-video-ffmpeg