"""DOVER over all 42 clusters the pipeline's own redundancy stage produces.

Why this matters: the application metric in the article scores delivered quality
with Q-Align, which is also the reference of the in-domain axis. That makes the
two non-independent. DOVER shares no architecture and no training data with
Q-Align and takes no part in the acceptance rule, so scoring delivered quality
with it breaks that specific dependency.
"""
import json, math, subprocess, sys, tempfile, time
from pathlib import Path

import torch, yaml
import numpy as np

N = Path(__file__).resolve().parent
DOVER_ROOT = N / "vendor" / "DOVER"
sys.path.insert(0, str(N / "vendor" / "python-deps"))
import os; os.chdir(DOVER_ROOT)
sys.path.insert(0, str(DOVER_ROOT))
from dover.datasets import UnifiedFrameSampler, spatial_temporal_view_decomposition
from dover.models import DOVER

VID = Path("/data/projects/platform/data/dataset")
CL = json.load(open(N / "clusters_all.json"))
OUT = N / "dover42_scores.json"

FULL = yaml.safe_load(open(DOVER_ROOT / "dover.yml"))
opt = FULL["data"]["val-l1080p"]["args"]
dev = torch.device("cuda")
model = DOVER(**FULL["model"]["args"]).to(dev)
model.load_state_dict(torch.load(FULL["test_load_path"], map_location=dev))
model.eval()
mean = torch.FloatTensor([123.675, 116.28, 103.53])
std = torch.FloatTensor([58.395, 57.12, 57.375])
samplers = {}
for st, so in opt["sample_types"].items():
    if "t_frag" not in so:
        samplers[st] = UnifiedFrameSampler(so["clip_len"], so["num_clips"], so["frame_interval"])
    else:
        samplers[st] = UnifiedFrameSampler(so["clip_len"] // so["t_frag"], so["t_frag"],
                                           so["frame_interval"], so["num_clips"])

scores = json.load(open(OUT)) if OUT.exists() else {}
t0 = time.time()
with tempfile.TemporaryDirectory() as td:
    for topic, clusters in CL.items():
        for ci, c in enumerate(clusters):
            for s in c:
                key = f"{topic}|{s['stem']}|{s['a']}|{s['b']}"
                if key in scores:
                    continue
                src = VID / topic / f"{s['stem']}.mp4"
                cut = Path(td) / "seg.mp4"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(s["a"]),
                                "-to", str(s["b"]), "-i", str(src), "-c:v", "libx264",
                                "-preset", "ultrafast", "-an", str(cut)], check=True)
                try:
                    views, _ = spatial_temporal_view_decomposition(str(cut), opt["sample_types"], samplers)
                    for k, v in views.items():
                        nc = opt["sample_types"][k].get("num_clips", 1)
                        views[k] = (((v.permute(1, 2, 3, 0) - mean) / std).permute(3, 0, 1, 2)
                                    .reshape(v.shape[0], nc, -1, *v.shape[2:])
                                    .transpose(0, 1).to(dev))
                    with torch.no_grad():
                        out = [r.mean().item() for r in model(views)]
                    scores[key] = {"technical": out[0], "aesthetic": out[1],
                                   "overall": out[0] + out[1]}
                except Exception as e:
                    print(f"  ERR {key}: {type(e).__name__}: {str(e)[:60]}", flush=True)
                    scores[key] = None
            json.dump(scores, open(OUT, "w"), indent=1)
            print(f"  {topic}#{ci} ok ({time.time()-t0:.0f}s)", flush=True)
print("FIM", flush=True)
