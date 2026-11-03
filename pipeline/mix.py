"""Place each narration clip at its start time on a silent track the length of the video.
usage: python3 -I mix.py <job_dir>  ->  <job_dir>/vo/voice_track.wav
"""
import json, os, sys
import numpy as np, soundfile as sf

job = os.path.abspath(sys.argv[1])
tl = json.load(open(os.path.join(job, "timeline.json")))
sr, clips = None, []
for v in tl["vo"]:
    a, r = sf.read(os.path.join(job, "vo", f"L{v['line']}.wav"), dtype="float32")
    sr = sr or r
    assert r == sr
    clips.append((v["start"], a))
n = int(round(tl["frames"] / tl["fps"] * sr))
track = np.zeros(n, dtype=np.float32)
f = int(0.008 * sr)  # 8 ms fades so clip edges never click
for start, a in clips:
    i = int(round(start * sr))
    a = a.copy()
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    seg = a[: max(0, n - i)]
    track[i:i + len(seg)] += seg
print("voice track", round(n / sr, 2), "s, peak", round(float(np.abs(track).max()), 3))
sf.write(os.path.join(job, "vo", "voice_track.wav"), track, sr)
