"""SIFT+BoVW on the synthetic ground truth, over a declared random subsample.

The deployed method is approximately 44--152 times slower than the still-image
candidates, so it is evaluated on a random subsample of 20 of the 83 segments,
drawn with seed 42 and listed in the output. Every other method uses all 83.
With 20 segments and 5 levels there are 100 binary clusters per degradation
type, which is ample for the prediction that matters: P2 says the deployed score
*inverts* on noise, and an inversion is a large effect.

Design A pairs {original, degraded}, so the vocabulary and the IDF are fitted
per pair with N = 2 documents, exactly as the pipeline fits them per redundancy
cluster. Fitting once per segment over all 41 conditions would give N = 41 and a
non-degenerate IDF, which is precisely the degeneracy the experiment exists to
expose, so it is not done.

Robustness: every failure mode observed in development is caught and logged
rather than allowed to kill the run, results are checkpointed after each
segment, and JSON is written atomically so a kill mid-write cannot corrupt it.
"""
import sys, json, os, time, traceback
from math import log10
from collections import Counter
from pathlib import Path

import numpy as np
import cv2
from sklearn.cluster import KMeans

sys.path.insert(0, "/dados/MESTRADO-USP/open-video-summary")
from open_video_summary.utils.processing.image import ImageProcessor

HERE = Path(__file__).resolve().parent
SYN = HERE / "synth_frames"
OUT = HERE / "synth_sift.json"
LOG = HERE / "synth_sift_failures.log"
K = 300
N_SEG = 20
SEED = 42

segs_all = sorted(d.name for d in SYN.iterdir() if d.is_dir() and (d / "orig").exists())
rng = np.random.default_rng(SEED)
subset = sorted(rng.choice(segs_all, size=min(N_SEG, len(segs_all)), replace=False).tolist())
print(f"{len(segs_all)} segments available; subsample of {len(subset)} (seed {SEED})", flush=True)
for s in subset:
    print(f"    {s}", flush=True)


def gray(d):
    return [cv2.imread(str(p), cv2.IMREAD_GRAYSCALE) for p in sorted(d.glob("*.png"))]


def save(obj):
    """Atomic: a kill mid-write cannot leave a truncated file."""
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(OUT)


def note(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    print("  ! " + msg, flush=True)


res = json.load(open(OUT)) if OUT.exists() else {"_subset": subset, "_seed": SEED, "_K": K, "data": {}}
res.setdefault("data", {})
data = res["data"]

t0 = time.time()
for si, seg in enumerate(subset):
    if seg in data:
        print(f"[skip] {seg}", flush=True)
        continue
    base = SYN / seg / "orig"
    try:
        gb = gray(base)
        if len(gb) < 3:
            note(f"{seg}: only {len(gb)} frames, skipped")
            data[seg] = {}
            save(res)
            continue
        db = ImageProcessor.ks_sift(gb)
    except Exception as e:
        note(f"{seg}/orig ks_sift failed: {type(e).__name__}: {e}")
        data[seg] = {}
        save(res)
        continue

    per = {}
    for c in sorted((SYN / seg).iterdir()):
        if not c.is_dir() or c.name == "orig":
            continue
        try:
            gd = gray(c)
            if len(gd) < 3:
                note(f"{seg}/{c.name}: only {len(gd)} frames")
                continue
            dd = ImageProcessor.ks_sift(gd)
        except Exception as e:
            note(f"{seg}/{c.name} ks_sift failed: {type(e).__name__}: {e}")
            continue

        pool = np.concatenate([db, dd])
        k_eff = K
        if len(pool) < K:
            # a heavily degraded copy can yield very few descriptors; K-means
            # requires n_samples >= n_clusters. Reduce K and record it.
            k_eff = max(2, len(pool) // 2)
            note(f"{seg}/{c.name}: only {len(pool)} descriptors, K reduced {K}->{k_eff}")
        try:
            km = KMeans(n_clusters=k_eff, random_state=42, n_init=1).fit(pool)
            tf = {"orig": Counter(km.predict(db)), "deg": Counter(km.predict(dd))}
        except Exception as e:
            note(f"{seg}/{c.name} kmeans failed: {type(e).__name__}: {e}")
            continue

        n_docs = 2
        df = Counter(w for x in tf.values() for w in x)
        out = {}
        for nm, x in tf.items():
            sb = sum(n * log10(k_eff / df[w]) for w, n in x.items())
            sf = sum(n * (0.0 if df[w] >= n_docs else log10(n_docs / df[w])) for w, n in x.items())
            out[nm] = {"bovw_sum": sb, "bovw_fixed": sf,
                       "n_desc": int(len(db) if nm == "orig" else len(dd))}
        out["_K"] = k_eff
        per[c.name] = out
        print(f"      {seg[:34]:<36} {c.name:<10} {len(dd):5d} desc  "
              f"({time.time()-t0:.0f}s total)", flush=True)

    data[seg] = per
    save(res)
    el = time.time() - t0
    eta = (len(subset) - si - 1) * el / (si + 1)
    print(f"[{si+1}/{len(subset)}] {seg}: {len(per)} conditions "
          f"({el/60:.1f} min elapsed, ETA {eta/60:.0f} min)", flush=True)

print(f"FIM: {sum(len(v) for v in data.values())} (segment, condition) scored "
      f"in {(time.time()-t0)/60:.1f} min", flush=True)
