"""P8: the reference model's own competence on the constructed ground truth.

Every in-domain agreement figure in the article is measured against Q-Align, so
the article asserts rather than measures that the reference is competent on
broadcast content. Design A has a correct answer by construction, which makes
that competence measurable. A value below 0.90 weakens every claim that rests on
the reference, and the article must then report it.

Same 20 segments as the deployed method, so the comparison is like-for-like.
Segment score is the mean over frames, per Equation (2).
"""
import sys, json, os, time
from pathlib import Path

import numpy as np
import cv2

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

SYN = HERE / "synth_frames"
OUT = HERE_arq("synth_qalign.json")

sys.path.insert(0, "/data/projects/benchmark")
os.chdir("/data/projects/benchmark")
import qalign_scorer

sift = json.load(open(HERE_arq("synth_sift.json")))
subset = set(sift["_subset"])

conds = {}
for seg in sorted(SYN.iterdir()):
    if not seg.is_dir() or seg.name not in subset:
        continue
    for c in sorted(seg.iterdir()):
        if c.is_dir() and any(c.glob("*.png")):
            conds[f"{seg.name}|{c.name}"] = c
print(f"{len(conds)} (segment, condition) pairs over {len(subset)} segments", flush=True)

res = json.load(open(OUT)) if OUT.exists() else {}
model = qalign_scorer.load_model(device="cuda")


def save():
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(res, f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(OUT)


t0 = time.time()
done = 0
for k, d in conds.items():
    if k in res:
        continue
    frames = [cv2.imread(str(p)) for p in sorted(d.glob("*.png"))]
    vals = []
    B = 8
    for i in range(0, len(frames), B):
        try:
            vals.extend(float(x) for x in
                        qalign_scorer.score_frames(frames[i:i + B], model, device="cuda"))
        except Exception as e:
            print(f"  ! {k} batch {i}: {type(e).__name__}: {e}", flush=True)
    res[k] = float(np.mean(vals)) if vals else None
    done += 1
    if done % 20 == 0:
        save()
        el = time.time() - t0
        left = sum(1 for x in conds if x not in res)
        print(f"  {len(res)}/{len(conds)} ({el/60:.1f} min, ETA {left*el/done/60:.0f} min)",
              flush=True)

save()
print(f"FIM qalign: {len(res)} scored in {(time.time()-t0)/60:.1f} min", flush=True)

