"""Score every segment of the 42 redundancy clusters the pipeline itself finds.

The 15 clusters used elsewhere in the article come from the six topics with
human redundancy annotations. Running the pipeline's own Stage-3 redundancy
component over the full 21-topic collection yields 42 clusters across 19 topics,
which is the set the deployed system would actually face. Scoring all of them
serves two purposes: it raises the in-domain sample by a factor of 2.8, and it
supplies the material for the end-to-end summary comparison.

Frames are extracted once per segment at 1 FPS and reused by every method.
"""
import sys, json, gc, time, math
from pathlib import Path

import numpy as np
import cv2
import torch

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

DS = Path("/dados/Projetos/sumarizador/data/dataset")
CL = json.load(open(HERE_arq("clusters_all.json")))
OUT = HERE_arq("e2e_scores.json")

# canonical segment key
def key(topic, s):
    return f"{topic}|{s['stem']}|{s['a']}|{s['b']}"


segs = {}
for topic, clusters in CL.items():
    for ci, c in enumerate(clusters):
        for s in c:
            segs[key(topic, s)] = (DS / topic / f"{s['stem']}.mp4", s["a"], s["b"])
print(f"{sum(len(v) for v in CL.values())} clusters, {len(segs)} distinct segments", flush=True)


CACHE = HERE / "e2e_frames"
CACHE.mkdir(exist_ok=True)


def _decode(path, a, b, target_fps=1.0):
    """Same 1 FPS sampling the benchmark harness uses."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return []
    src = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(src / target_fps)))
    out, i = [], 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        t = i / src
        i += 1
        if t < a:
            continue
        if t > b:
            break
        if (i - 1) % step:
            continue
        out.append(img)
    cap.release()
    return out


def frames(path, a, b):
    """Decode once, then serve every method from the same frames on disk, so
    no difference between methods can come from the frames each one saw."""
    tag = f"{Path(path).parent.name}__{Path(path).stem}__{a}_{b}"
    d = CACHE / tag
    if d.exists():
        return [cv2.imread(str(p)) for p in sorted(d.glob("*.png"))]
    fr = _decode(path, a, b)
    tmp = CACHE / (tag + ".part")
    tmp.mkdir(exist_ok=True)
    for i, f in enumerate(fr):
        cv2.imwrite(str(tmp / f"{i:04d}.png"), f)
    tmp.rename(d)
    return fr


res = json.load(open(OUT)) if OUT.exists() else {}

PYIQA = ["liqe", "qualiclip", "niqe", "brisque", "musiq", "topiq_nr", "clipiqa", "clipiqa+"]
todo = [m for m in PYIQA if m not in res]
if todo:
    import pyiqa
    dev = torch.device("cuda")
    # cache frames on first pass only
    for m in todo:
        t0 = time.time()
        metric = pyiqa.create_metric(m, device=dev)
        per = {}
        with torch.no_grad():
            for n, (p, a, b) in segs.items():
                fr = frames(p, a, b)
                if not fr:
                    per[n] = None
                    continue
                vals = []
                for f in fr:
                    rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                    t = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255).unsqueeze(0).to(dev)
                    try:
                        vals.append(float(metric(t).item()))
                    except Exception:
                        pass
                per[n] = float(np.mean(vals)) if vals else None
        res[m] = per
        json.dump(res, open(OUT, "w"), indent=1)
        print(f"[ok] {m}: {len(per)} segments in {time.time()-t0:.0f}s", flush=True)
        del metric
        gc.collect()
        torch.cuda.empty_cache()

# ── Q-Align, the reference model ──────────────────────────────────────────
if "qalign" not in res:
    sys.path.insert(0, "/dados/Projetos/quality-benchmark")
    import qalign_scorer
    t0 = time.time()
    model = qalign_scorer.load_model(device="cuda")
    per = {}
    for n, (p, a, b) in segs.items():
        fr = frames(p, a, b)
        if not fr:
            per[n] = None
            continue
        try:
            sc = qalign_scorer.score_frames(fr, model, device="cuda")
            per[n] = float(np.mean(sc)) if len(sc) else None
        except Exception as e:
            print(f"  qalign failed on {n}: {e}", flush=True)
            per[n] = None
    res["qalign"] = per
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"[ok] qalign: {len(per)} segments in {time.time()-t0:.0f}s", flush=True)
    del model
    gc.collect()
    torch.cuda.empty_cache()

print("FIM", flush=True)

