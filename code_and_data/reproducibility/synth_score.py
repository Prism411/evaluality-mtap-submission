"""Score the synthetic in-domain ground truth.

Designs A (paired accuracy) and B (level ordering) need one segment-level score
per (segment, condition). Every method here is frame-wise, so the segment score
is the mean over its frames, exactly as Equation (2) of the article specifies.

Order matters: the cheap NR-IQA methods first so partial results are usable,
SIFT+BoVW last because it is the slow one.
"""
import sys, json, gc, time
from pathlib import Path

import numpy as np
import cv2
import torch

HERE = Path(__file__).resolve().parent
SYN = HERE / "synth_frames"
OUT = HERE / "synth_scores.json"

# the same 20 segments the deployed method was run on, so every comparison is
# like-for-like rather than resting on different material
import numpy as _np
_all = sorted(d.name for d in SYN.iterdir() if d.is_dir() and (d / "orig").exists())
_sub = set(_np.random.default_rng(42).choice(_all, size=20, replace=False).tolist())
conds = {}
for seg in sorted(SYN.iterdir()):
    if not seg.is_dir() or seg.name not in _sub:
        continue
    for c in sorted(seg.iterdir()):
        if c.is_dir() and any(c.glob("*.png")):
            conds[f"{seg.name}|{c.name}"] = c
print(f"{len(conds)} (segment, condition) pairs", flush=True)

res = json.load(open(OUT)) if OUT.exists() else {}


def frames(d):
    return [cv2.imread(str(p)) for p in sorted(d.glob("*.png"))]


import pyiqa
dev = torch.device("cuda")
ORDER = ["brisque", "niqe", "qualiclip", "liqe", "clipiqa", "clipiqa+",
         "topiq_nr", "musiq", "dbcnn", "hyperiqa", "arniqa"]

for m in ORDER:
    tag = m.replace("+", "_plus")
    if tag in res:
        print(f"[skip] {tag}", flush=True)
        continue
    t0 = time.time()
    try:
        metric = pyiqa.create_metric(m, device=dev)
    except Exception as e:
        print(f"[ERR] {m}: {e}", flush=True)
        continue
    per = {}
    with torch.no_grad():
        for i, (k, d) in enumerate(conds.items()):
            vals = []
            for f in frames(d):
                rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                t = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255).unsqueeze(0).to(dev)
                try:
                    vals.append(float(metric(t).item()))
                except Exception:
                    pass
            per[k] = float(np.mean(vals)) if vals else None
            if (i + 1) % 400 == 0:
                el = time.time() - t0
                print(f"  {m}: {i+1}/{len(conds)} ({el:.0f}s, ETA {(len(conds)-i-1)*el/(i+1):.0f}s)", flush=True)
    res[tag] = per
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"[ok] {tag}: {len(per)} in {time.time()-t0:.0f}s", flush=True)
    del metric
    gc.collect()
    torch.cuda.empty_cache()

print("FIM", flush=True)

