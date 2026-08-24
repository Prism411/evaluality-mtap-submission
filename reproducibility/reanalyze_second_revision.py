#!/usr/bin/env python3
"""Construct-validity and scale-sensitivity analyses for the second revision.

This script performs no model inference.  It uses the saved segment-level
scores to:

* separate the technical and aesthetic DOVER branches from the uncalibrated
  branch sum used in the first end-to-end analysis;
* report raw, global-range, per-cluster-position and selected-maximum
  estimands for the 42 operational clusters;
* quantify sensitivity to clusters with small DOVER ranges; and
* audit ties, the exclusion of darkening/desaturation, and descriptor-count
  changes in the 800 construction-defined original--degraded comparisons.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np


SEED = 42
N_BOOT = 10_000
HERE = Path(__file__).resolve().parent
CANONICAL_MANUSCRIPT = (
    Path("/dados/Projetos/memoria-agentes/07-Artigos")
    / "evaluality-webmedia-2026"
    / "mtap"
)
MANUSCRIPT = HERE if (HERE / "e2e_sift.json").exists() else CANONICAL_MANUSCRIPT
DERIVED = MANUSCRIPT / "derived_data"
OUTPUT = MANUSCRIPT / "second_revision_reanalysis.json"


def load_json(path: Path) -> Any:
    with path.open() as stream:
        return json.load(stream)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def interval(values: list[float] | np.ndarray) -> list[float]:
    return [float(value) for value in np.percentile(values, [2.5, 97.5])]


def quantiles(values: list[float] | np.ndarray) -> dict[str, float]:
    labels = ("min", "q10", "q25", "median", "q75", "q90", "max")
    points = (0, 10, 25, 50, 75, 90, 100)
    return {
        label: float(value)
        for label, value in zip(labels, np.percentile(values, points), strict=True)
    }


def application_analysis() -> dict[str, Any]:
    clusters: dict[str, dict[str, Any]] = load_json(MANUSCRIPT / "e2e_sift.json")
    model_scores: dict[str, dict[str, float]] = load_json(
        MANUSCRIPT / "e2e_scores.json"
    )
    dover: dict[str, dict[str, float]] = load_json(
        MANUSCRIPT / "dover42_scores.json"
    )
    cluster_ids = list(clusters)
    topics: dict[str, list[str]] = defaultdict(list)
    for cluster in cluster_ids:
        topics[cluster.split("#", maxsplit=1)[0]].append(cluster)
    topic_names = sorted(topics)

    def choose(cluster: str, method: str) -> str:
        candidates = list(clusters[cluster])
        if method == "sift_bovw":
            return max(
                candidates,
                key=lambda segment: clusters[cluster][segment]["bovw_sum"],
            )
        return max(candidates, key=lambda segment: model_scores[method][segment])

    def records(sample: list[str], method: str, branch: str) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for cluster in sample:
            candidates = list(clusters[cluster])
            values = np.array([dover[segment][branch] for segment in candidates])
            selected = float(dover[choose(cluster, method)][branch])
            low = float(values.min())
            high = float(values.max())
            spread = high - low
            position = np.nan if spread <= 1e-12 else 100.0 * (selected - low) / spread
            ordered = np.sort(values)
            if len(ordered) == 1:
                rank_position = 100.0
            else:
                rank_position = 100.0 * float(np.searchsorted(ordered, selected, side="right") - 1) / (len(ordered) - 1)
            rows.append(
                {
                    "selected": selected,
                    "low": low,
                    "high": high,
                    "range": spread,
                    "cluster_position": position,
                    "rank_position": rank_position,
                    "selected_maximum": float(np.isclose(selected, high, rtol=0, atol=1e-12)),
                }
            )
        return rows

    def estimands(sample: list[str], method: str, branch: str) -> dict[str, float]:
        rows = records(sample, method, branch)
        selected = np.array([row["selected"] for row in rows])
        low = np.array([row["low"] for row in rows])
        high = np.array([row["high"] for row in rows])
        positions = np.array([row["cluster_position"] for row in rows])
        denominator = float(high.mean() - low.mean())
        global_range = np.nan if denominator <= 1e-12 else 100.0 * float(selected.mean() - low.mean()) / denominator
        return {
            "raw_mean": float(selected.mean()),
            "global_achievable_range_percent": float(global_range),
            "mean_cluster_position_percent": float(np.nanmean(positions)),
            "mean_rank_position_percent": float(
                np.mean([row["rank_position"] for row in rows])
            ),
            "selected_maximum_percent": float(
                100.0 * np.mean([row["selected_maximum"] for row in rows])
            ),
        }

    rng = np.random.default_rng(SEED)
    topic_samples: list[list[str]] = []
    hierarchical_samples: list[list[str]] = []
    for _ in range(N_BOOT):
        sampled_topics = rng.choice(topic_names, size=len(topic_names), replace=True)
        topic_samples.append(
            [cluster for topic in sampled_topics for cluster in topics[topic]]
        )
        hierarchical: list[str] = []
        for topic in sampled_topics:
            observed = topics[topic]
            hierarchical.extend(
                rng.choice(observed, size=len(observed), replace=True).tolist()
            )
        hierarchical_samples.append(hierarchical)

    methods = ("sift_bovw", "liqe", "qualiclip", "clipiqa+")
    branches = ("technical", "aesthetic", "overall")
    result: dict[str, Any] = {}
    for branch in branches:
        branch_ranges = [
            max(dover[segment][branch] for segment in clusters[cluster])
            - min(dover[segment][branch] for segment in clusters[cluster])
            for cluster in cluster_ids
        ]
        branch_result: dict[str, Any] = {
            "range_distribution": quantiles(branch_ranges),
            "zero_range_clusters": int(sum(value <= 1e-12 for value in branch_ranges)),
            "methods": {},
            "liqe_minus_sift": {},
            "range_sensitivity": {},
        }
        for method in methods:
            branch_result["methods"][method] = estimands(cluster_ids, method, branch)

        metric_names = tuple(branch_result["methods"]["liqe"])
        point_liqe = branch_result["methods"]["liqe"]
        point_sift = branch_result["methods"]["sift_bovw"]
        topic_differences: list[dict[str, float]] = []
        for sample in topic_samples:
            liqe_sample = estimands(sample, "liqe", branch)
            sift_sample = estimands(sample, "sift_bovw", branch)
            topic_differences.append(
                {metric: liqe_sample[metric] - sift_sample[metric] for metric in metric_names}
            )
        hierarchical_differences: list[dict[str, float]] = []
        for sample in hierarchical_samples:
            liqe_sample = estimands(sample, "liqe", branch)
            sift_sample = estimands(sample, "sift_bovw", branch)
            hierarchical_differences.append(
                {metric: liqe_sample[metric] - sift_sample[metric] for metric in metric_names}
            )
        for metric in metric_names:
            topic_values = [sample[metric] for sample in topic_differences]
            hierarchical_values = [sample[metric] for sample in hierarchical_differences]
            branch_result["liqe_minus_sift"][metric] = {
                "estimate": float(point_liqe[metric] - point_sift[metric]),
                "topic_block_ci95": interval(topic_values),
                "hierarchical_ci95": interval(hierarchical_values),
            }

        for quantile_name, percentile in (("exclude_bottom_10pct", 10), ("exclude_bottom_25pct", 25)):
            threshold = float(np.percentile(branch_ranges, percentile))
            retained = [
                cluster
                for cluster, spread in zip(cluster_ids, branch_ranges, strict=True)
                if spread > threshold
            ]
            liqe_est = estimands(retained, "liqe", branch)
            sift_est = estimands(retained, "sift_bovw", branch)
            branch_result["range_sensitivity"][quantile_name] = {
                "range_threshold": threshold,
                "clusters_retained": len(retained),
                "global_achievable_range_difference": float(
                    liqe_est["global_achievable_range_percent"]
                    - sift_est["global_achievable_range_percent"]
                ),
                "raw_mean_difference": float(
                    liqe_est["raw_mean"] - sift_est["raw_mean"]
                ),
                "selected_maximum_difference_pp": float(
                    liqe_est["selected_maximum_percent"]
                    - sift_est["selected_maximum_percent"]
                ),
            }
        result[branch] = branch_result

    sum_error = max(
        abs(value["overall"] - value["technical"] - value["aesthetic"])
        for value in dover.values()
    )
    return {
        "n_topics": len(topic_names),
        "n_clusters": len(cluster_ids),
        "changed_selections_liqe_vs_sift": int(
            sum(choose(cluster, "liqe") != choose(cluster, "sift_bovw") for cluster in cluster_ids)
        ),
        "dover_configuration": {
            "checkpoint_config": "official DOVER dover.yml and test_load_path",
            "view_config": "data.val-l1080p.args.sample_types",
            "stored_outputs": "raw model outputs; overall is the uncalibrated technical+aesthetic sum",
            "maximum_sum_identity_error": float(sum_error),
            "not_used": "the official post-hoc ITU-standardized fused score was not computed",
        },
        "branches": result,
    }


def constructed_pair_analysis() -> dict[str, Any]:
    sift_path = DERIVED / "synth_sift.json"
    scores_path = DERIVED / "synth_scores.json"
    qalign_path = DERIVED / "synth_qalign.json"
    sift = load_json(sift_path)
    scores: dict[str, dict[str, float]] = load_json(scores_path)
    scores["qalign"] = load_json(qalign_path)
    subset: list[str] = sift["_subset"]
    conditions = [
        f"{distortion}_{level}"
        for distortion in ("blur", "dark", "h264", "jpeg", "motion", "noise", "rescale", "satur")
        for level in range(1, 6)
    ]
    directions = {method: method not in {"brisque", "niqe"} for method in scores}

    def compare(original: float, degraded: float, higher_better: bool) -> int:
        if np.isclose(original, degraded, rtol=0, atol=1e-12):
            return 0
        if higher_better:
            return 1 if original > degraded else -1
        return 1 if original < degraded else -1

    def model_outcomes(method: str, included_types: set[str] | None = None) -> list[int]:
        outcomes: list[int] = []
        for segment in subset:
            original = scores[method][f"{segment}|orig"]
            for condition in conditions:
                distortion = condition.rsplit("_", maxsplit=1)[0]
                if included_types is not None and distortion not in included_types:
                    continue
                degraded = scores[method][f"{segment}|{condition}"]
                outcomes.append(compare(original, degraded, directions[method]))
        return outcomes

    def sift_outcomes(included_types: set[str] | None = None) -> list[int]:
        outcomes: list[int] = []
        for segment in subset:
            for condition in conditions:
                distortion = condition.rsplit("_", maxsplit=1)[0]
                if included_types is not None and distortion not in included_types:
                    continue
                pair = sift["data"][segment][condition]
                outcomes.append(
                    compare(pair["orig"]["bovw_sum"], pair["deg"]["bovw_sum"], True)
                )
        return outcomes

    retained_types = {"blur", "h264", "jpeg", "motion", "noise", "rescale"}
    methods: dict[str, Any] = {}
    all_outcomes = {"sift_bovw": sift_outcomes()}
    all_outcomes.update({method: model_outcomes(method) for method in scores})
    restricted_outcomes = {"sift_bovw": sift_outcomes(retained_types)}
    restricted_outcomes.update(
        {method: model_outcomes(method, retained_types) for method in scores}
    )
    for method in ("sift_bovw", *sorted(scores)):
        full = all_outcomes[method]
        restricted = restricted_outcomes[method]
        methods[method] = {
            "all_8_types": {
                "n": len(full),
                "correct": int(sum(value == 1 for value in full)),
                "incorrect": int(sum(value == -1 for value in full)),
                "ties": int(sum(value == 0 for value in full)),
                "strict_accuracy": float(100.0 * sum(value == 1 for value in full) / len(full)),
            },
            "excluding_darkening_and_desaturation": {
                "n": len(restricted),
                "correct": int(sum(value == 1 for value in restricted)),
                "incorrect": int(sum(value == -1 for value in restricted)),
                "ties": int(sum(value == 0 for value in restricted)),
                "strict_accuracy": float(
                    100.0 * sum(value == 1 for value in restricted) / len(restricted)
                ),
            },
        }

    count_by_type: dict[str, list[float]] = defaultdict(list)
    count_increase_by_type: dict[str, list[bool]] = defaultdict(list)
    count_by_type_level: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for segment in subset:
        for condition in conditions:
            distortion, level = condition.rsplit("_", maxsplit=1)
            pair = sift["data"][segment][condition]
            delta = float(pair["deg"]["n_desc"] - pair["orig"]["n_desc"])
            count_by_type[distortion].append(delta)
            count_increase_by_type[distortion].append(delta > 0)
            count_by_type_level[distortion][level].append(delta)

    descriptor_counts = {}
    for distortion in sorted(count_by_type):
        descriptor_counts[distortion] = {
            "mean_degraded_minus_original": float(np.mean(count_by_type[distortion])),
            "median_degraded_minus_original": float(np.median(count_by_type[distortion])),
            "pairs_with_increased_count_percent": float(
                100.0 * np.mean(count_increase_by_type[distortion])
            ),
            "mean_delta_by_level": {
                level: float(np.mean(values))
                for level, values in sorted(count_by_type_level[distortion].items())
            },
        }

    topic_counts = Counter(segment.split("__", maxsplit=1)[0] for segment in subset)
    return {
        "n_segments": len(subset),
        "n_topics_represented": len(topic_counts),
        "segments_per_topic": dict(sorted(topic_counts.items())),
        "construction": {
            "all_types": "unmodified member versus a deterministic transformed member",
            "interpretation": "construction-defined signal fidelity, not human perceptual preference",
            "sensitivity_exclusion": "darkening and desaturation excluded",
        },
        "tie_policy": "ties count as neither correct nor incorrect; strict accuracy uses correct/n",
        "methods": methods,
        "descriptor_count_diagnostics": descriptor_counts,
        "input_sha256": {
            sift_path.name: sha256(sift_path),
            scores_path.name: sha256(scores_path),
            qalign_path.name: sha256(qalign_path),
        },
    }


def main() -> None:
    result = {
        "metadata": {
            "seed": SEED,
            "bootstrap_resamples": N_BOOT,
            "model_inference_performed": False,
        },
        "application": application_analysis(),
        "constructed_pairs": constructed_pair_analysis(),
    }
    with OUTPUT.open("w") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
