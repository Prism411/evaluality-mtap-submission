"""In-domain BoVW variants and keypoint density on the 15 redundancy clusters.

Answers two of the reviewer's open items at once:
  (a) r_ab measured in-domain, with the vocabulary and the IDF estimated per
      cluster exactly as the deployed pipeline does, instead of being carried
      over from the image databases;
  (b) the frame-normalized BoVW variants that the article defines but has not
      run, so the sum-vs-mean objection can be settled rather than argued.

Uses the pipeline's own SIFT keyframe selection (ImageProcessor.ks_sift), so
the descriptors are the ones the deployed system would see.
"""
import sys, json, time
from math import log10
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

sys.path.insert(0, "/dados/MESTRADO-USP/open-video-summary")
from open_video_summary.utils.processing.video import VideoProcessor
from open_video_summary.utils.processing.image import ImageProcessor

HERE = Path(__file__).resolve().parent

# ⛔ MEDIDO EM 08/09 rodando o pacote de um clone: este script lia `HERE_arq("x.json")` e os
# insumos derivados moram em `derived_data/`. Sem esta resolucao o pacote traz um script
# que nao acha o proprio dado. A pasta do script continua tendo prioridade.
_HERE0 = HERE


def HERE_arq(nome):
    for base in (_HERE0, _HERE0 / 'derived_data'):
        if (base / nome).exists():
            return base / nome
    return _HERE0 / nome

CL = json.load(open(HERE_arq("indomain_clusters.json")))["clusters"]
DICT_SIZE = 300
OUT = HERE_arq("indomain_bovw.json")

print(f"{len(CL)} clusters, {sum(len(c['segs']) for c in CL)} segments", flush=True)

results = json.load(open(OUT)) if OUT.exists() else {}
t0 = time.time()
for c in CL:
    key = f"{c['topic']}#{c['idx']}"
    if key in results:
        print(f"[skip] {key}", flush=True)
        continue
    feats, meta = {}, {}
    for s in c["segs"]:
        sid = f"{s['stem']}:{s['a']:.1f}-{s['b']:.1f}"
        frames = VideoProcessor.retrieve_video_frames(
            s["path"], grayscale=True, start_second=s["a"], end_second=s["b"])
        if len(frames) < 3:
            continue
        try:
            d = ImageProcessor.ks_sift(frames)
        except Exception as e:
            print(f"  ks_sift failed on {sid}: {e}", flush=True)
            continue
        feats[sid] = d
        # keypoint density: mean SIFT keypoints per frame over ALL frames,
        # the baseline the article compares BoVW against
        import cv2
        sift = cv2.SIFT_create()
        kp = [len(sift.detect(f, None) or []) for f in frames]
        meta[sid] = {"n_desc": int(len(d)), "n_frames": len(frames),
                     "kp_density": float(np.mean(kp)) if kp else 0.0,
                     "duration": s["b"] - s["a"]}
        print(f"    {sid}: {len(frames)} frames, {len(d)} desc, "
              f"kp/frame {meta[sid]['kp_density']:.0f} ({time.time()-t0:.0f}s)", flush=True)

    if len(feats) < 2:
        print(f"[skip] {key}: {len(feats)} usable segments", flush=True)
        continue

    # same call the deployed pipeline makes: sklearn's default initialization
    km = KMeans(n_clusters=DICT_SIZE, random_state=42)
    km.fit(np.concatenate(list(feats.values())))
    tfs = {sid: Counter(km.predict(d)) for sid, d in feats.items()}
    n_docs = len(feats)
    df = Counter(w for t in tfs.values() for w in t)

    per = {}
    for sid, tf in tfs.items():
        s_buggy = s_fixed = 0.0
        for w, n in tf.items():
            s_buggy += n * log10(DICT_SIZE / df[w])
            s_fixed += n * (0.0 if df[w] >= n_docs else log10(n_docs / df[w]))
        m = meta[sid]
        per[sid] = {
            "bovw_sum": s_buggy,                       # the deployed scoring method
            "bovw_fixed": s_fixed,                     # corrected IDF, still a sum
            "bovw_per_frame": s_buggy / max(1, m["n_frames"]),
            "bovw_per_desc": s_buggy / max(1, m["n_desc"]),
            "bovw_fixed_per_frame": s_fixed / max(1, m["n_frames"]),
            "bovw_fixed_per_desc": s_fixed / max(1, m["n_desc"]),
            **m,
        }
    results[key] = per
    json.dump(results, open(OUT, "w"), indent=1)   # checkpoint after each cluster
    print(f"[ok] {key}: {len(per)} segments ({time.time()-t0:.0f}s)", flush=True)

json.dump(results, open(OUT, "w"), indent=1)
print("FIM", flush=True)

