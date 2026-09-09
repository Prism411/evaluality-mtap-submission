#!/usr/bin/env python3
"""Combine matched-operation and DOVER constructed-pair controls.

No model inference is performed here.  The script turns the checkpointed raw
outputs into the manuscript-facing selection counts, DOVER-T estimands and
dependency-aware intervals used in the third revision.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

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

MANUSCRIPT = Path(
    "/dados/Projetos/memoria-agentes/07-Artigos/"
    "evaluality-webmedia-2026/mtap"
)
MATCHED = HERE_arq("same_frame_same_pooling_control.json")
DOVER_PAIRS = HERE_arq("dover_constructed_pairs.json")
OUTPUT = MANUSCRIPT / "third_revision_reanalysis.json"
SEED = 42
N_BOOT = 10_000


def load(path: Path) -> Any:
    with open(path) as stream:
        return json.load(stream)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def interval(values) -> list[float]:
    return [float(value) for value in np.percentile(values, [2.5, 97.5])]


def matched_analysis() -> dict[str, Any]:
    control = load(MATCHED)
    if len(control["clusters"]) != 42:
        raise RuntimeError(f"matched control incomplete: {len(control['clusters'])}/42 clusters")
    dover = load(MANUSCRIPT / "dover42_scores.json")
    original_liqe = load(MANUSCRIPT / "e2e_scores.json")["liqe"]
    clusters = list(control["clusters"])
    topics: dict[str, list[str]] = defaultdict(list)
    for cluster in clusters:
        topics[cluster.split("#", 1)[0]].append(cluster)
    topic_names = sorted(topics)

    def selected(cluster: str, field: str) -> str:
        return control["clusters"][cluster]["selected"][field]

    original_changes = {
        cluster
        for cluster in clusters
        if selected(cluster, "published_deployed")
        != max(
            control["clusters"][cluster]["segments"],
            key=lambda segment: original_liqe[segment],
        )
    }

    regimes = {
        "uniform_1fps_capped10_mean": ("sift_matched_mean", "liqe_matched_mean"),
    }

    def rows(sample: list[str], field: str) -> list[dict[str, float]]:
        output = []
        for cluster in sample:
            candidates = list(control["clusters"][cluster]["segments"])
            values = np.array([dover[candidate]["technical"] for candidate in candidates])
            chosen = dover[selected(cluster, field)]["technical"]
            low, high = float(values.min()), float(values.max())
            output.append(
                {
                    "selected": float(chosen),
                    "low": low,
                    "high": high,
                    "selected_maximum": float(np.isclose(chosen, high, rtol=0, atol=1e-12)),
                }
            )
        return output

    def estimands(sample: list[str], field: str) -> dict[str, float]:
        values = rows(sample, field)
        chosen = np.array([row["selected"] for row in values])
        low = np.array([row["low"] for row in values])
        high = np.array([row["high"] for row in values])
        denominator = float(high.mean() - low.mean())
        return {
            "raw_mean": float(chosen.mean()),
            "global_achievable_range_percent": float(
                100 * (chosen.mean() - low.mean()) / denominator
            ),
            "selected_maximum_percent": float(
                100 * np.mean([row["selected_maximum"] for row in values])
            ),
        }

    rng = np.random.default_rng(SEED)
    topic_samples = []
    hierarchical_samples = []
    for _ in range(N_BOOT):
        sampled_topics = rng.choice(topic_names, size=len(topic_names), replace=True)
        topic_samples.append(
            [cluster for topic in sampled_topics for cluster in topics[topic]]
        )
        hierarchical = []
        for topic in sampled_topics:
            observed = topics[topic]
            hierarchical.extend(
                rng.choice(observed, size=len(observed), replace=True).tolist()
            )
        hierarchical_samples.append(hierarchical)

    results = {}
    for name, (sift_field, liqe_field) in regimes.items():
        disagreements = {
            cluster
            for cluster in clusters
            if selected(cluster, sift_field) != selected(cluster, liqe_field)
        }
        point_sift = estimands(clusters, sift_field)
        point_liqe = estimands(clusters, liqe_field)
        differences = {
            metric: point_liqe[metric] - point_sift[metric]
            for metric in point_sift
        }
        topic_values = {metric: [] for metric in differences}
        hierarchy_values = {metric: [] for metric in differences}
        for sample in topic_samples:
            s = estimands(sample, sift_field)
            l = estimands(sample, liqe_field)
            for metric in differences:
                topic_values[metric].append(l[metric] - s[metric])
        for sample in hierarchical_samples:
            s = estimands(sample, sift_field)
            l = estimands(sample, liqe_field)
            for metric in differences:
                hierarchy_values[metric].append(l[metric] - s[metric])
        results[name] = {
            "sift_field": sift_field,
            "liqe_field": liqe_field,
            "sift_liqe_disagreements": len(disagreements),
            "disagreement_clusters": sorted(disagreements),
            "overlap_with_original_22": len(disagreements & original_changes),
            "sift_dover_technical": point_sift,
            "liqe_dover_technical": point_liqe,
            "liqe_minus_sift": {
                metric: {
                    "estimate": float(differences[metric]),
                    "topic_block_ci95": interval(topic_values[metric]),
                    "hierarchical_ci95": interval(hierarchy_values[metric]),
                }
                for metric in differences
            },
        }

    return {
        "n_clusters": len(clusters),
        "n_topics": len(topics),
        "published_liqe_vs_deployed_changes": len(original_changes),
        "published_change_clusters": sorted(original_changes),
        "sampling_summary": control["summary"],
        "regimes": results,
    }


def main() -> None:
    dover_pairs = load(DOVER_PAIRS)
    if len(dover_pairs["segments"]) != 20:
        raise RuntimeError(f"DOVER pair control incomplete: {len(dover_pairs['segments'])}/20 segments")
    result = {
        "metadata": {
            "seed": SEED,
            "bootstrap_resamples": N_BOOT,
            "model_inference_performed_by_this_script": False,
            "input_sha256": {
                MATCHED.name: sha256(MATCHED),
                DOVER_PAIRS.name: sha256(DOVER_PAIRS),
                "dover42_scores.json": sha256(MANUSCRIPT / "dover42_scores.json"),
            },
        },
        "same_frame_same_pooling": matched_analysis(),
        "dover_technical_constructed_pairs": dover_pairs["summary"],
        "dover_technical_configuration": dover_pairs["configuration"],
    }
    with open(OUTPUT, "w") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
