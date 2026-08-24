#!/usr/bin/env python3
"""Reanalyse the two dependence-sensitive axes requested in major revision.

Outputs a single JSON with:

* KADID-10k distortion sensitivity computed within each reference image and
  block-bootstrapped over the 81 references;
* in-domain agreement and delivered-reference scores block-bootstrapped over
  the 19 news topics;
* a hierarchical topic-to-cluster sensitivity analysis for the end-to-end
  contrast.

No model inference is performed here.  Per-image and per-segment scores must
already exist in the paths declared below.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


SEED = 42
N_BOOT = 10_000
PROJECT_DIR = Path(__file__).resolve().parent
KADID_META = PROJECT_DIR / "data" / "kadid10k" / "kadid10k" / "dmos.csv"
KADID_CACHE = PROJECT_DIR / "results" / "kadid10k" / "scores_cache"
MANUSCRIPT_DIR = (
    Path("/dados/Projetos/memoria-agentes/07-Artigos/")
    / "evaluality-webmedia-2026"
    / "mtap"
)
OUTPUT = MANUSCRIPT_DIR / "major_revision_reanalysis.json"
DATASET = Path("/dados/Projetos/sumarizador/data/dataset")
WORD_COUNTS = MANUSCRIPT_DIR / "segment_word_counts.json"

# True means that a larger raw score denotes better quality.  Sensitivity to
# increasing distortion is therefore -rho(score, level) for these methods.
METHODS: dict[str, tuple[str, bool]] = {
    "qalign": ("Q-Align", True),
    "qualiclip": ("QualiCLIP", True),
    "liqe": ("LIQE", True),
    "clipiqa_plus": ("CLIP-IQA+", True),
    "arniqa": ("ARNIQA", True),
    "tres": ("TReS", True),
    "maniqa": ("MANIQA", True),
    "topiq_nr": ("TOPIQ", True),
    "musiq": ("MUSIQ", True),
    "dbcnn": ("DBCNN", True),
    "niqe": ("NIQE", False),
    "hyperiqa": ("HyperIQA", True),
    "brisque": ("BRISQUE", False),
    "clipiqa": ("CLIP-IQA", True),
    "si": ("SI", True),
    "kp_density": ("Keypoint density", True),
    "sift_bovw": ("SIFT+BoVW", True),
    "dinov2": ("DINOv2", True),
    "resnet50": ("ResNet-50", True),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile_interval(values: np.ndarray) -> list[float]:
    return [float(x) for x in np.percentile(values, [2.5, 97.5])]


def load_kadid() -> pd.DataFrame:
    metadata = pd.read_csv(KADID_META)
    parts = metadata["dist_img"].str.extract(
        r"I(?P<reference>\d+)_(?P<distortion>\d+)_(?P<level>\d+)\.png"
    )
    if parts.isna().any().any():
        raise ValueError("Unexpected KADID image identifier")
    return metadata.assign(
        image_name=metadata["dist_img"],
        reference=parts["reference"].astype(int),
        distortion=parts["distortion"].astype(int),
        level=parts["level"].astype(int),
    )


def kadid_sensitivity(metadata: pd.DataFrame) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    reference_ids = sorted(metadata["reference"].unique())
    distortion_ids = sorted(metadata["distortion"].unique())
    output: dict[str, Any] = {}

    for cache_name, (display_name, higher_is_better) in METHODS.items():
        cache_path = KADID_CACHE / f"{cache_name}.csv"
        if not cache_path.is_file():
            print(f"skipping missing per-image cache: {cache_path}")
            continue
        scored = metadata.merge(
            pd.read_csv(cache_path), on="image_name", how="inner", validate="one_to_one"
        )
        if len(scored) != len(metadata):
            raise ValueError(f"Incomplete cache for {display_name}: {len(scored)} rows")

        by_reference = np.empty((len(reference_ids), len(distortion_ids)))
        for i, reference in enumerate(reference_ids):
            for j, distortion in enumerate(distortion_ids):
                group = scored[
                    (scored["reference"] == reference)
                    & (scored["distortion"] == distortion)
                ].sort_values("level")
                if len(group) != 5:
                    raise ValueError(
                        f"Expected five levels for {display_name}, ref={reference}, "
                        f"distortion={distortion}"
                    )
                rho = spearmanr(group["level"], group["score"]).statistic
                # A constant score is an absence of sensitivity, not a missing
                # observation.  Dropping it would bias a method upward.
                if not np.isfinite(rho):
                    rho = 0.0
                method_polarity = 1 if higher_is_better else -1
                target_polarity = -1  # larger KADID level means worse quality
                by_reference[i, j] = method_polarity * target_polarity * rho

        per_type = by_reference.mean(axis=0)
        indices = rng.integers(
            0, len(reference_ids), size=(N_BOOT, len(reference_ids))
        )
        boot_per_type = by_reference[indices].mean(axis=1)
        boot_mean = boot_per_type.mean(axis=1)
        boot_count = (boot_per_type > 0.5).sum(axis=1)

        pooled = []
        for distortion in distortion_ids:
            group = scored[scored["distortion"] == distortion]
            rho = spearmanr(group["level"], group["score"]).statistic
            if not np.isfinite(rho):
                rho = 0.0
            method_polarity = 1 if higher_is_better else -1
            target_polarity = -1
            pooled.append(method_polarity * target_polarity * rho)

        human_srcc = spearmanr(scored["score"], scored["dmos"]).statistic
        # Despite its column name, KADID documents this [1,5] opinion field as
        # higher-is-better.  Preserve the sign rather than taking abs(rho).
        human_direction_aligned_srcc = (1 if higher_is_better else -1) * human_srcc
        output[cache_name] = {
            "display_name": display_name,
            "n_references": len(reference_ids),
            "n_distortion_types": len(distortion_ids),
            "within_reference_mean": float(per_type.mean()),
            "within_reference_mean_ci95": percentile_interval(boot_mean),
            "types_above_0_5": int((per_type > 0.5).sum()),
            "types_above_0_5_ci95": [
                int(x) for x in np.percentile(boot_count, [2.5, 97.5])
            ],
            "per_type": [float(x) for x in per_type],
            "per_type_ci95": [
                percentile_interval(boot_per_type[:, j])
                for j in range(len(distortion_ids))
            ],
            "legacy_pooled_mean": float(np.mean(pooled)),
            "legacy_pooled_types_above_0_5": int(sum(x > 0.5 for x in pooled)),
            "kadid_srcc": float(human_srcc),
            "kadid_target_polarity": 1,
            "kadid_direction_aligned_srcc": float(human_direction_aligned_srcc),
            "cache_sha256": sha256(cache_path),
        }

    return output


def kadid_paired_equivalence(metadata: pd.DataFrame) -> dict[str, Any]:
    """Paired block bootstrap for the canonical BoVW/keypoint comparison."""
    merged = metadata[["image_name", "reference", "dmos"]].merge(
        pd.read_csv(KADID_CACHE / "sift_bovw_fixed.csv"),
        on="image_name",
        validate="one_to_one",
    ).rename(columns={"score": "sift_bovw_fixed"})
    merged = merged.merge(
        pd.read_csv(KADID_CACHE / "kp_density.csv"),
        on="image_name",
        validate="one_to_one",
    ).rename(columns={"score": "kp_density"})
    reference_indices = [
        merged.index[merged["reference"] == reference].to_numpy()
        for reference in sorted(merged["reference"].unique())
    ]

    def associations(indices: np.ndarray) -> tuple[float, float]:
        sift = float(
            spearmanr(
                merged.loc[indices, "sift_bovw_fixed"],
                merged.loc[indices, "dmos"],
            ).statistic
        )
        keypoints = float(
            spearmanr(
                merged.loc[indices, "kp_density"], merged.loc[indices, "dmos"]
            ).statistic
        )
        return sift, keypoints

    all_indices = merged.index.to_numpy()
    point_sift, point_keypoints = associations(all_indices)
    rng = np.random.default_rng(SEED)
    boot = np.empty((N_BOOT, 2))
    for resample in range(N_BOOT):
        sampled = rng.integers(0, len(reference_indices), len(reference_indices))
        indices = np.concatenate([reference_indices[index] for index in sampled])
        boot[resample] = associations(indices)
    difference = boot[:, 0] - boot[:, 1]
    margin = 0.02
    difference_interval = percentile_interval(difference)
    return {
        "n_references": len(reference_indices),
        "sift_bovw_fixed_srcc": point_sift,
        "sift_bovw_fixed_block_ci95": percentile_interval(boot[:, 0]),
        "kp_density_srcc": point_keypoints,
        "kp_density_block_ci95": percentile_interval(boot[:, 1]),
        "paired_difference": point_sift - point_keypoints,
        "paired_difference_block_ci95": difference_interval,
        "equivalence_margin": margin,
        "ci_entirely_inside_equivalence_margin": bool(
            difference_interval[0] > -margin and difference_interval[1] < margin
        ),
    }


def load_json(name: str) -> Any:
    with (MANUSCRIPT_DIR / name).open() as stream:
        return json.load(stream)


def in_domain_reanalysis() -> dict[str, Any]:
    clusters: dict[str, dict[str, Any]] = load_json("e2e_sift.json")
    method_scores: dict[str, dict[str, float]] = load_json("e2e_scores.json")
    extension_path = MANUSCRIPT_DIR / "e2e_scores_major_revision.json"
    if extension_path.is_file():
        with extension_path.open() as stream:
            extension_scores: dict[str, dict[str, float]] = json.load(stream)
        method_scores.update(extension_scores)
    dover_raw: dict[str, dict[str, float]] = load_json("dover42_scores.json")
    references = {
        "dover": {key: value["overall"] for key, value in dover_raw.items()},
        "qalign": method_scores["qalign"],
    }
    lower_is_better = {"brisque", "niqe"}
    topics: dict[str, list[str]] = defaultdict(list)
    for cluster_id in clusters:
        topics[cluster_id.split("#", maxsplit=1)[0]].append(cluster_id)
    topic_names = sorted(topics)
    if WORD_COUNTS.is_file():
        word_count_cache: dict[str, int] = {
            key: int(value) for key, value in load_json(WORD_COUNTS.name).items()
        }
    else:
        word_count_cache = {}

    def segment_words(segment: str) -> int:
        if segment in word_count_cache:
            return word_count_cache[segment]
        topic, stem, start_text, end_text = segment.split("|")
        cache_key = (topic, stem, float(start_text), float(end_text))
        for path in sorted((DATASET / topic).glob("*.json")):
            try:
                records = json.loads(path.read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(records, list):
                continue
            video = next(
                (record for record in records if record.get("name") == stem), None
            )
            if video is None:
                continue
            for transcript_segment in video.get("segments", []):
                start = float(transcript_segment.get("start", 0))
                end = float(transcript_segment.get("end", 0))
                if abs(start - cache_key[2]) < 1e-6 and abs(end - cache_key[3]) < 1e-6:
                    count = len(re.findall(r"\w+", transcript_segment.get("content", "")))
                    word_count_cache[segment] = count
                    return count
        raise KeyError(f"Transcript segment not found: {segment}")

    def select(cluster_id: str, method: str) -> str:
        candidates = list(clusters[cluster_id])
        if method == "sift_bovw":
            return max(
                candidates,
                key=lambda segment: clusters[cluster_id][segment]["bovw_sum"],
            )
        if method == "sift_per_frame":
            return max(
                candidates,
                key=lambda segment: clusters[cluster_id][segment]["bovw_per_frame"],
            )
        chooser: Callable[..., str] = min if method in lower_is_better else max
        return chooser(candidates, key=lambda segment: method_scores[method][segment])

    def kappa_uniform(sample: list[str], method: str) -> float:
        observed = np.mean(
            [select(cluster, method) == select(cluster, "qalign") for cluster in sample]
        )
        expected = np.mean([1.0 / len(clusters[cluster]) for cluster in sample])
        return float((observed - expected) / (1.0 - expected))

    def delivered(sample: list[str], method: str, reference: str) -> float:
        scores = references[reference]
        selected = []
        best = []
        worst = []
        for cluster in sample:
            candidates = list(clusters[cluster])
            values = [scores[segment] for segment in candidates]
            selected.append(scores[select(cluster, method)])
            best.append(max(values))
            worst.append(min(values))
        denominator = np.mean(best) - np.mean(worst)
        return float(100.0 * (np.mean(selected) - np.mean(worst)) / denominator)

    all_clusters = list(clusters)
    methods = ["sift_bovw", "sift_per_frame", *sorted(method_scores)]
    rng = np.random.default_rng(SEED)
    topic_samples: list[list[str]] = []
    hierarchical_samples: list[list[str]] = []
    for _ in range(N_BOOT):
        sampled_topics = rng.choice(topic_names, size=len(topic_names), replace=True)
        topic_sample = [cluster for topic in sampled_topics for cluster in topics[topic]]
        topic_samples.append(topic_sample)

        hierarchical_sample: list[str] = []
        for topic in sampled_topics:
            topic_clusters = topics[topic]
            hierarchical_sample.extend(
                rng.choice(topic_clusters, size=len(topic_clusters), replace=True).tolist()
            )
        hierarchical_samples.append(hierarchical_sample)

    agreement: dict[str, Any] = {}
    delivered_results: dict[str, Any] = {}
    selection_summary: dict[str, Any] = {}
    for method in methods:
        selected_segments = [select(cluster, method) for cluster in all_clusters]
        selected_by_qalign = [select(cluster, "qalign") for cluster in all_clusters]
        selected_by_sift = [select(cluster, "sift_bovw") for cluster in all_clusters]
        selection_summary[method] = {
            "changed_vs_sift_bovw": int(
                sum(a != b for a, b in zip(selected_segments, selected_by_sift))
            ),
            "duration_seconds": float(
                sum(
                    float(segment.split("|")[3]) - float(segment.split("|")[2])
                    for segment in selected_segments
                )
            ),
            "transcript_words": int(sum(segment_words(segment) for segment in selected_segments)),
        }
        point_kappa = kappa_uniform(all_clusters, method)
        topic_kappa = np.array(
            [kappa_uniform(sample, method) for sample in topic_samples]
        )
        agreement[method] = {
            "agreement_count": int(
                sum(a == b for a, b in zip(selected_segments, selected_by_qalign))
            ),
            "n_clusters": len(all_clusters),
            "kappa_uniform": point_kappa,
            "topic_block_ci95": percentile_interval(topic_kappa),
            "topic_block_probability_above_zero": float(np.mean(topic_kappa > 0)),
        }

        delivered_results[method] = {}
        for reference in references:
            point = delivered(all_clusters, method, reference)
            topic_values = np.array(
                [delivered(sample, method, reference) for sample in topic_samples]
            )
            hierarchy_values = np.array(
                [
                    delivered(sample, method, reference)
                    for sample in hierarchical_samples
                ]
            )
            delivered_results[method][reference] = {
                "estimate": point,
                "topic_block_ci95": percentile_interval(topic_values),
                "hierarchical_ci95": percentile_interval(hierarchy_values),
            }

    contrasts: dict[str, Any] = {}
    for method in sorted(method_scores):
        contrasts[method] = {}
        for reference in references:
            point = delivered(all_clusters, method, reference) - delivered(
                all_clusters, "sift_bovw", reference
            )
            topic_values = np.array(
                [
                    delivered(sample, method, reference)
                    - delivered(sample, "sift_bovw", reference)
                    for sample in topic_samples
                ]
            )
            hierarchy_values = np.array(
                [
                    delivered(sample, method, reference)
                    - delivered(sample, "sift_bovw", reference)
                    for sample in hierarchical_samples
                ]
            )
            contrasts[method][reference] = {
                "estimate": point,
                "topic_block_ci95": percentile_interval(topic_values),
                "topic_block_probability_above_zero": float(
                    np.mean(topic_values > 0)
                ),
                "hierarchical_ci95": percentile_interval(hierarchy_values),
                "hierarchical_probability_above_zero": float(
                    np.mean(hierarchy_values > 0)
                ),
            }

    WORD_COUNTS.write_text(
        json.dumps(dict(sorted(word_count_cache.items())), indent=2) + "\n"
    )
    return {
        "n_topics": len(topic_names),
        "n_clusters": len(all_clusters),
        "agreement": agreement,
        "selection_summary": selection_summary,
        "delivered_reference_scores": delivered_results,
        "paired_contrasts_vs_sift_bovw": contrasts,
    }


def main() -> None:
    result = {
        "metadata": {
            "seed": SEED,
            "bootstrap_resamples": N_BOOT,
            "kadid_resampling_unit": "reference image",
            "in_domain_primary_resampling_unit": "news topic",
            "in_domain_sensitivity_resampling": "news topic then cluster",
            "constant_within_reference_score": "direction-aligned rho set to zero",
        },
        "kadid_within_reference": kadid_sensitivity(load_kadid()),
        "kadid_paired_equivalence": kadid_paired_equivalence(load_kadid()),
        "in_domain": in_domain_reanalysis(),
    }
    with OUTPUT.open("w") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
