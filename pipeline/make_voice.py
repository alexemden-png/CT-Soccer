"""Narration: one Kokoro TTS clip per line of spec.json "narration", silence trimmed.
usage: python3 -I make_voice.py <job_dir>
Writes <job_dir>/vo/L1.wav .. L4.wav and vo/durations.json.
"""
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

job = os.path.abspath(sys.argv[1])
spec = json.load(open(os.path.join(job, "spec.json")))
kdir = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro"))
k = Kokoro(os.path.join(kdir, "kokoro-v1.0.onnx"), os.path.join(kdir, "voices-v1.0.bin"))
voice = spec.get("voice", "af_heart")   # the CT Soccer Hub voice
speed = float(spec.get("speed", 1.0))
lines = spec["narration"]
assert len(lines) == 4, "narration must have exactly 4 lines (hook, facts, extra, call to action)"

out = os.path.join(job, "vo")
os.makedirs(out, exist_ok=True)
info = []
for i, text in enumerate(lines):
    samples, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
    a = np.asarray(samples, dtype=np.float32)
    env = np.abs(a)
    idx = np.where(env > 0.01 * env.max())[0]
    pad = int(0.04 * sr)  # keep 40 ms of breath room
    a = a[max(0, idx[0] - pad): min(len(a), idx[-1] + pad)]
    sf.write(os.path.join(out, f"L{i+1}.wav"), a, sr)
    d = len(a) / sr
    info.append({"line": i + 1, "dur": round(d, 3), "words": len(text.split()), "sr": sr})
    print(f"L{i+1}: {d:5.2f}s  {len(text.split())/d:4.2f} words/s | {text}")
json.dump(info, open(os.path.join(out, "durations.json"), "w"), indent=1)
total = sum(x["dur"] for x in info)
print(f"speech total {total:.1f}s (aim for 13-17s so the video lands at 18-22s)")
