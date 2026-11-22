#!/bin/bash
# Uso: ./render2.sh es|en  -> ../camus_edit_v2_<lang>.mp4  (versión corta y dinámica, 120 BPM)
set -e
T="$(cd "$(dirname "$0")" && pwd)"; L=${1:-es}; P=${P:-4}
[ -d "$T/src" ] || python3 "$T/prep_sources.py"
[ -d "$T/clips" ] || python3 "$T/prep_clips.py"
N=$(EDIT_LANG=$L python3 "$T/edit2.py" info | awk '/frames/{print $4}'); step=$(( (N + P - 1) / P ))
TMP="$(mktemp -d)"; : > "$TMP/list.txt"
for i in $(seq 0 $((P-1))); do
  a=$((i*step)); b=$(( (i+1)*step )); [ $b -gt $N ] && b=$N
  EDIT_LANG=$L python3 "$T/edit2.py" render $a $b "$TMP/seg_$i.mp4" > "$TMP/log_$i.txt" 2>&1 &
  echo "file '$TMP/seg_$i.mp4'" >> "$TMP/list.txt"
done
wait
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$TMP/master.mp4"
ffmpeg -v error -y -i "$TMP/master.mp4" -c:v libx264 -preset slow -b:v 9M -maxrate 14M -bufsize 18M -pass 1 -passlogfile "$TMP/p" -an -f null /dev/null
ffmpeg -v error -y -i "$TMP/master.mp4" -c:v libx264 -preset slow -b:v 9M -maxrate 14M -bufsize 18M -pass 2 -passlogfile "$TMP/p" -pix_fmt yuv420p -profile:v high -movflags +faststart -an "$T/../camus_edit_v2_$L.mp4"
echo "ok -> $T/../camus_edit_v2_$L.mp4"
