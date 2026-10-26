"""ARNIQA, MANIQA and TReS on the three image databases.

MANIQA and TReS were previously left out on cost grounds, which the article
cannot use as an exclusion criterion after declaring cost non-discriminating
among candidates. ARNIQA is added because a 2026 benchmark that evaluates no
method published after its reference model has a coverage gap.
"""
import sys, gc, time, csv
from pathlib import Path

import torch, pyiqa

HERE = Path(__file__).resolve().parent
ROOT = Path("/data/projects/benchmark")
DB = {
    "kadid": (ROOT / "data/kadid10k/kadid10k/images", "*.png", HERE / "scores_kadid"),
    "koniq": (ROOT / "data/koniq10k/512x384", "*.jpg", HERE / "scores_koniq"),
    "clive": (HERE / "datasets/LIVEC/Images", "*", HERE / "scores_clive"),
}
dev = torch.device("cuda")
MODELS = ["arniqa"]   # multi-crop models dropped on the image databases; see paper

for db, (d, pat, out) in DB.items():
    if not d.exists():
        print(f"[skip db] {db}: {d} missing", flush=True)
        continue
    names = sorted(p.name for p in d.glob(pat) if p.suffix.lower() in (".png", ".jpg", ".bmp", ".jpeg"))
    print(f"{db}: {len(names)} images", flush=True)
    for m in MODELS:
        dst = out / f"{m}.csv"
        if dst.exists():
            print(f"  [skip] {db}/{m}", flush=True)
            continue
        t0 = time.time()
        try:
            metric = pyiqa.create_metric(m, device=dev)
        except Exception as e:
            print(f"  [ERR] {m}: {e}", flush=True)
            continue
        rows = []
        with torch.no_grad():
            for i, n in enumerate(names):
                try:
                    rows.append((n, float(metric(str(d / n)).item())))
                except Exception:
                    rows.append((n, float("nan")))
                if (i + 1) % 2000 == 0:
                    el = time.time() - t0
                    print(f"    {db}/{m}: {i+1}/{len(names)} ({(i+1)/el:.1f} img/s)", flush=True)
        out.mkdir(parents=True, exist_ok=True)
        with open(dst, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["image_name", "score"])
            w.writerows(rows)
        print(f"  [ok] {db}/{m}: {len(rows)} in {time.time()-t0:.0f}s", flush=True)
        del metric
        gc.collect()
        torch.cuda.empty_cache()
print("FIM", flush=True)

