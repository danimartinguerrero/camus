#!/bin/bash
# Uso: ./render.sh en|es   -> genera ../camus_edit_<lang>.mp4 (1080x1920, 30 fps, sin audio)
set -e
T="$(cd "$(dirname "$0")" && pwd)"; L=${1:-en}; N=1980; P=${P:-4}; step=$(( (N + P - 1) / P ))
[ -d "$T/src" ] || python3 "$T/prep_sources.py"
TMP="$(mktemp -d)"; : > "$TMP/list.txt"
for i in $(seq 0 $((P-1))); do
  a=$((i*step)); b=$(( (i+1)*step )); [ $b -gt $N ] && b=$N
  EDIT_LANG=$L python3 "$T/edit.py" render $a $b "$TMP/seg_$i.mp4" > "$TMP/log_$i.txt" 2>&1 &
  echo "file '$TMP/seg_$i.mp4'" >> "$TMP/list.txt"
done
wait
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$TMP/master.mp4"
ffmpeg -v error -y -i "$TMP/master.mp4" -c:v libx264 -preset slow -b:v 8M -maxrate 12M -bufsize 16M -pass 1 -passlogfile "$TMP/p" -an -f null /dev/null
ffmpeg -v error -y -i "$TMP/master.mp4" -c:v libx264 -preset slow -b:v 8M -maxrate 12M -bufsize 16M -pass 2 -passlogfile "$TMP/p" -pix_fmt yuv420p -profile:v high -movflags +faststart -an "$T/../camus_edit_$L.mp4"
echo "ok -> $T/../camus_edit_$L.mp4"
