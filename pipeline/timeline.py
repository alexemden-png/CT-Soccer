"""Beat timings and animation cues from the narration clip lengths.
usage: python3 -I timeline.py <job_dir>
Beats: 1 hook (3D stadium) | 2 card + fact rows | 3 stat / note | 4 end card.
A row or the stat appears when its "at": [line, "phrase"] is spoken; without "at", rows spread over line 2.
"""
import json, os, re, sys

job = os.path.abspath(sys.argv[1])
spec = json.load(open(os.path.join(job, "spec.json")))
dur = {d["line"]: d["dur"] for d in json.load(open(os.path.join(job, "vo", "durations.json")))}
lines = spec["narration"]

pads = [(0.25, 0.45), (0.30, 0.40), (0.30, 0.45), (0.60, 1.40)]  # (lead-in, pause after) per line
B, vo, t = [0.0], [], 0.0
for i, (lead, tail) in enumerate(pads, start=1):
    vo.append({"line": i, "start": round(t + lead, 3), "dur": dur[i]})
    t += lead + dur[i] + tail
    B.append(round(t, 3))


def wordcue(li, phrase):
    """Estimated start time of phrase in line li (by character share of the clip)."""
    words = re.findall(r"\S+", lines[li - 1])
    w = [len(re.sub(r"[^A-Za-z0-9]", "", x)) + (3 if re.search(r"[,:;.?!]$", x) else 0) + 1 for x in words]
    tot, acc, starts = sum(w), 0, []
    for x in w:
        starts.append(acc / tot)
        acc += x
    low = [re.sub(r"[^a-z0-9 -]", "", x.lower()) for x in words]
    ph = [re.sub(r"[^a-z0-9 -]", "", x) for x in phrase.lower().split()]
    for k in range(len(low)):
        if low[k:k + len(ph)] == ph:
            return round(vo[li - 1]["start"] + starts[k] * dur[li] * 0.97, 3)
    print(f"WARNING: phrase {phrase!r} not found in line {li}; using the default time")
    return None


cues, rows = {}, spec["card"]["rows"]
assert 2 <= len(rows) <= 4, "the card needs 2-4 rows"
v2 = vo[1]
for i, r in enumerate(rows):
    tt = wordcue(*r["at"]) if r.get("at") else None
    if tt is None:
        frac = 0.08 + 0.80 * (i / (len(rows) - 1))
        tt = v2["start"] + v2["dur"] * frac
    cues[f"row{i}"] = round(max(B[1] + 0.45, min(tt, B[3] - 0.6)), 3)
if spec.get("stat"):
    at = spec["stat"].get("at")
    tt = (wordcue(*at) if at else None) or vo[2]["start"] + 0.1
    cues["stat"] = round(min(tt, B[3] - 0.8), 3)
if spec.get("note"):
    cues["note"] = round(cues["stat"] + 0.9 if "stat" in cues else vo[2]["start"] + 0.2, 3)
cues["url"] = wordcue(4, "c t soccer hub") or round(vo[3]["start"] + 0.6, 3)

fps = 30
out = {"beats": B, "vo": vo, "cues": cues, "total": round(B[-1], 3), "fps": fps, "frames": int(round(B[-1] * fps))}
json.dump(out, open(os.path.join(job, "timeline.json"), "w"), indent=1)
print("beats", B, "| total", out["total"], "s,", out["frames"], "frames")
print("cues", cues)
