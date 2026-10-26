"""Score LIVE In the Wild (CLIVE) with every method in the study.

CLIVE is the third database: authentic distortions like KonIQ-10k, but no
released checkpoint in this study was fitted on it. The resulting contrasts are
descriptive because the databases and released model families are not matched.

Writes CSVs to scores_clive/ and a timing log to clive_timing.json.
Nothing in the benchmark repository is modified.
"""
import sys, os, json, time, gc, csv
from pathlib import Path

import numpy as np
import scipy.io as sio

REPO = Path("/data/projects/benchmark")
HERE = Path(__file__).resolve().parent
OUT = HERE / "scores_clive"
OUT.mkdir(exist_ok=True)
IMGS = HERE / "datasets/LIVEC/Images"

sys.path.insert(0, str(REPO))
os.chdir(REPO)  # the repo's scorers resolve sibling modules relative to cwd

import benchmark_koniq as bk

# redirect the repo's cache away from the repo itself
bk.CACHE_DIR = OUT
bk.RESULTS_DIR = OUT

d = HERE / "datasets/LIVEC/Data"
mos = sio.loadmat(d / "AllMOS_release.mat")["AllMOS_release"].ravel()
names = [str(x[0]) for x in sio.loadmat(d / "AllImages_release.mat")["AllImages_release"].ravel()]

# The first 7 images of the release are the training/orientation set, excluded
# by convention in every paper that reports on CLIVE.
names, mos = names[7:], mos[7:]
paths = [str(IMGS / n) for n in names]
missing = [p for p in paths if not Path(p).exists()]
assert not missing, f"{len(missing)} images missing, e.g. {missing[:3]}"
print(f"CLIVE: {len(paths)} images, MOS in [{mos.min():.2f}, {mos.max():.2f}]", flush=True)

json.dump({"names": names, "mos": mos.tolist()}, open(HERE / "clive_gt.json", "w"))

PYIQA = ["brisque", "niqe", "clipiqa", "clipiqa+", "liqe",
         "dbcnn", "hyperiqa", "musiq", "topiq_nr", "qualiclip"]
REPO_METHODS = ["dinov2", "resnet50", "kp_density", "si",
                "sift_bovw", "sift_bovw_fixed"] + list(bk._CNN_BOVW_SCORERS.keys())

timing = {}
tpath = HERE / "clive_timing.json"
if tpath.exists():
    timing = json.load(open(tpath))


def done(tag):
    return (OUT / f"{tag}.csv").exists()


def write(tag, scores):
    with open(OUT / f"{tag}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["image_name", "score"])
        w.writerows(zip(names, [float(s) for s in scores]))


# ── pyiqa metrics, one image at a time so the timing is per-image ──────────
import torch, pyiqa
dev = torch.device("cuda")

for m in PYIQA:
    tag = m.replace("+", "_plus")
    if done(tag):
        print(f"[skip] {tag}", flush=True)
        continue
    t0 = time.time()
    metric = pyiqa.create_metric(m, device=dev)
    rows = []
    with torch.no_grad():
        for i, p in enumerate(paths):
            try:
                rows.append(float(metric(p).item()))
            except Exception:
                rows.append(float("nan"))
            if (i + 1) % 300 == 0:
                el = time.time() - t0
                print(f"  {m}: {i+1}/{len(paths)} ({(i+1)/el:.1f} img/s)", flush=True)
    el = time.time() - t0
    write(tag, rows)
    timing[tag] = {"total_s": el, "n": len(paths), "ms_per_image": 1000 * el / len(paths)}
    json.dump(timing, open(tpath, "w"), indent=1)
    print(f"[ok] {tag}: {el:.0f}s = {1000*el/len(paths):.1f} ms/img", flush=True)
    del metric
    gc.collect()
    torch.cuda.empty_cache()

# ── repository scorers ────────────────────────────────────────────────────
for m in REPO_METHODS:
    if done(m):
        print(f"[skip] {m}", flush=True)
        continue
    t0 = time.time()
    try:
        scores = bk.SCORER_MAP[m](paths)
    except Exception as e:
        print(f"[ERR] {m}: {e}", flush=True)
        continue
    el = time.time() - t0
    write(m, scores)
    timing[m] = {"total_s": el, "n": len(paths), "ms_per_image": 1000 * el / len(paths)}
    json.dump(timing, open(tpath, "w"), indent=1)
    print(f"[ok] {m}: {el:.0f}s = {1000*el/len(paths):.1f} ms/img", flush=True)
    gc.collect()
    torch.cuda.empty_cache()

print("FIM", flush=True)
