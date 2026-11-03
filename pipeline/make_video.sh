#!/bin/bash
# Build one CT Soccer Hub spotlight video from <job_dir>/spec.json.
# usage: bash pipeline/make_video.sh <job_dir>
# Output: <job_dir>/<slug>.mp4 (1080x1920, 30 fps, voice at -14 LUFS) and <job_dir>/<slug>_sheet.jpg (6 frames to check).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
JOB="$(cd "$1" && pwd)"
SLUG=$(python3 -c "import json;print(json.load(open('$JOB/spec.json'))['slug'])")
cp "$HERE/spotlight/scene.html" "$HERE/render.js" "$JOB/"
ln -sfn "$HERE/node_modules" "$JOB/node_modules"

python3 -I "$HERE/make_voice.py" "$JOB"
python3 -I "$HERE/timeline.py" "$JOB"
python3 -I "$HERE/mix.py" "$JOB"
ffmpeg -v error -y -i "$JOB/vo/voice_track.wav" -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 "$JOB/vo/voice_track_norm.wav"

FR=$(python3 -c "import json;print(json.load(open('$JOB/timeline.json'))['frames'])")
HALF=$((FR / 2))
cd "$JOB"
# two halves in parallel (one per CPU core), then joined without re-encoding
node render.js chunk 0 "$HALF" c0.mp4 > render0.log 2>&1 &
P0=$!
node render.js chunk "$HALF" "$FR" c1.mp4 > render1.log 2>&1 &
P1=$!
wait $P0 || { echo "render of part 1 failed:"; tail -20 render0.log; exit 1; }
wait $P1 || { echo "render of part 2 failed:"; tail -20 render1.log; exit 1; }
grep -h "pageerror" render0.log render1.log && { echo "ERROR: the page threw errors (see above)"; exit 1; } || true
printf "file 'c0.mp4'\nfile 'c1.mp4'\n" > chunks.txt
ffmpeg -v error -y -f concat -safe 0 -i chunks.txt -c copy silent.mp4
ffmpeg -v error -y -i silent.mp4 -i vo/voice_track_norm.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -ar 48000 -shortest -movflags +faststart "$SLUG.mp4"

# checks: frame count, duration, size, and a 6-frame contact sheet
GOT=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$SLUG.mp4")
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SLUG.mp4")
SIZE=$(stat -c%s "$SLUG.mp4")
echo "frames $GOT (expected $FR), duration ${DUR}s, size $((SIZE / 1024)) KB"
[ "$GOT" -ge $((FR - 2)) ] || { echo "ERROR: frames missing"; exit 1; }
TS=$(python3 -c "
import json;t=json.load(open('timeline.json'));B=t['beats'];C=t['cues']
rows=sorted(v for k,v in C.items() if k.startswith('row'))
pts=[min(1.2,B[1]-0.3),rows[-1]+0.5,(C.get('stat',B[2]+0.3))+0.9,B[3]-0.4,B[3]+1.4,B[4]-0.3]
print(' '.join(f'{p:.2f}' for p in pts))")
i=0
for t in $TS; do ffmpeg -v error -y -ss "$t" -i "$SLUG.mp4" -frames:v 1 -vf scale=360:-1 "sheet_$i.jpg"; i=$((i + 1)); done
ffmpeg -v error -y -i sheet_0.jpg -i sheet_1.jpg -i sheet_2.jpg -i sheet_3.jpg -i sheet_4.jpg -i sheet_5.jpg -filter_complex hstack=6 "${SLUG}_sheet.jpg"
rm -f sheet_?.jpg c0.mp4 c1.mp4 chunks.txt
echo "OK $JOB/$SLUG.mp4  (look at ${SLUG}_sheet.jpg; frames at $TS s)"
