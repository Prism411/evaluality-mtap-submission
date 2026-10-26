"""The application question: does changing the scoring method change the summary?

For each of the 19 topics with at least one redundancy cluster, the pipeline's
Stage-4 decision is taken twice, once under the deployed scoring method and once
under each candidate. Summaries are then compared on three things:

  1. how many of the delivered segments differ at all;
  2. the visual quality of what is delivered, scored by the independent
     reference model, which is the quantity the criterion exists to maximize;
  3. whether the transcript changes. Cluster membership is an operational
     redundancy decision and does not establish identical semantic utility.

Also recomputes the in-domain agreement axis on all 42 clusters, which is 2.8
times the sample used elsewhere in the article.
"""
import json, math, re
from pathlib import Path

import numpy as np

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

DS = Path("/data/projects/platform/data/dataset")
CL = json.load(open(HERE_arq("clusters_all.json")))
SC = json.load(open(HERE_arq("e2e_scores.json")))

LOWER = {"niqe", "brisque"}          # lower is better
REF = "qalign"


def key(topic, s):
    return f"{topic}|{s['stem']}|{s['a']}|{s['b']}"


def pick(method, topic, cluster):
    vals = {}
    for s in cluster:
        v = SC.get(method, {}).get(key(topic, s))
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        vals[key(topic, s)] = -v if method in LOWER else v
    if len(vals) < 2:
        return None
    return max(vals, key=vals.get)


methods = [m for m in SC if m != REF]
clusters = [(t, c) for t, cs in CL.items() for c in cs]
print(f"{len(clusters)} clusters over {len(CL)} topics; methods: {sorted(SC)}")

# ── agreement axis on all 42 clusters ─────────────────────────────────────
usable = [(t, c) for t, c in clusters if pick(REF, t, c) is not None]
pe = float(np.mean([1 / len(c) for _, c in usable]))
print(f"\n=== in-domain agreement, {len(usable)} clusters, chance floor {pe:.4f} ===")
print(f"{'method':<14}{'agree':>10}{'kappa':>9}{'95% CI':>20}")
rows = {}
for m in sorted(methods):
    hit = n = 0
    for t, c in usable:
        p = pick(m, t, c)
        if p is None:
            continue
        n += 1
        hit += (p == pick(REF, t, c))
    if not n:
        continue
    po = hit / n
    k = (po - pe) / (1 - pe)
    se = math.sqrt(max(po * (1 - po), 1e-9) / n) / (1 - pe)
    rows[m] = dict(agree=hit, n=n, kappa=k, lo=k - 1.96 * se, hi=k + 1.96 * se, se=se)
    print(f"{m:<14}{hit:>5}/{n:<4}{k:>9.3f}   [{k-1.96*se:+.2f}, {k+1.96*se:+.2f}]")

# ── the application comparison ────────────────────────────────────────────
# SIFT+BoVW is not among the pyiqa methods scored here; its per-cluster choice
# comes from the pipeline's own scoring, recomputed below from the published
# in-domain results where available and from the descriptor count otherwise.
print("\n=== summary-level comparison: LIQE against the reference and against each other ===")
for a in sorted(methods):
    for b in sorted(methods):
        if a >= b:
            continue
        diff = sum(1 for t, c in usable if pick(a, t, c) != pick(b, t, c))
        if a in ("liqe",) or b in ("liqe",):
            print(f"  {a:<12} vs {b:<12} differ on {diff:>2}/{len(usable)} clusters")

# ── delivered quality under each scoring method ───────────────────────────
print("\n=== quality of what is delivered, scored by the reference model ===")
print(f"{'scoring method':<16}{'mean ref score':>16}{'vs oracle':>12}{'vs worst':>12}")
oracle = np.mean([SC[REF][pick(REF, t, c)] for t, c in usable])
worst = np.mean([min(SC[REF][key(t, s)] for s in c
                     if SC[REF].get(key(t, s)) is not None) for t, c in usable])
for m in sorted(methods):
    vals = []
    for t, c in usable:
        p = pick(m, t, c)
        if p is None or SC[REF].get(p) is None:
            continue
        vals.append(SC[REF][p])
    if not vals:
        continue
    mu = float(np.mean(vals))
    print(f"{m:<16}{mu:>16.4f}{mu-oracle:>12.4f}{mu-worst:>12.4f}")
print(f"{'(oracle)':<16}{oracle:>16.4f}{0.0:>12.4f}{oracle-worst:>12.4f}")
print(f"{'(worst-case)':<16}{worst:>16.4f}{worst-oracle:>12.4f}{0.0:>12.4f}")

json.dump({"chance": pe, "n_clusters": len(usable), "rows": rows,
           "oracle": float(oracle), "worst": float(worst)},
          open(HERE_arq("e2e_analysis.json"), "w"), indent=1)
