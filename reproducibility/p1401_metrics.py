#!/usr/bin/env python3
"""Recompute the ITU-T P.1401 metrics from cached per-image scores.

The script fits the four-parameter logistic mapping used by the manuscript and
reports PLCC (linearity), RMSE (accuracy), outlier ratio (consistency) and the
confidence-interval-discounted RMSE*.  It only reads public ground truth and
cached scores; no model inference is performed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import chi2, norm, rankdata


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_DIR / "results" / "major_revision" / "p1401_metrics.json"


def logistic(
    score: np.ndarray,
    beta_1: float,
    beta_2: float,
    beta_3: float,
    beta_4: float,
) -> np.ndarray:
    exponent = np.clip(beta_2 * (score - beta_3), -700, 700)
    return beta_1 * (0.5 - 1.0 / (1.0 + np.exp(exponent))) + beta_4


def fit_mapping(score: np.ndarray, opinion: np.ndarray) -> np.ndarray:
    initial = [
        opinion.max() - opinion.min(),
        1.0 / (score.std() + 1e-9),
        float(np.median(score)),
        float(opinion.mean()),
    ]
    try:
        parameters, _ = curve_fit(
            logistic, score, opinion, p0=initial, maxfev=40_000
        )
        return logistic(score, *parameters)
    except (RuntimeError, ValueError, FloatingPointError):
        design = np.vstack([score, np.ones_like(score)]).T
        slope, intercept = np.linalg.lstsq(design, opinion, rcond=None)[0]
        return slope * score + intercept


def fisher_interval(correlation: float, n: int) -> list[float]:
    correlation = float(np.clip(correlation, -0.999999, 0.999999))
    critical = norm.ppf(0.975)
    transformed = np.arctanh(correlation)
    half_width = critical / np.sqrt(n - 3)
    return [
        float(value)
        for value in np.tanh(
            [transformed - half_width, transformed + half_width]
        )
    ]


def rmse_interval(rmse: float, n: int, parameters: int = 4) -> list[float]:
    degrees = n - parameters
    return [
        float(rmse * np.sqrt(degrees / chi2.ppf(0.975, degrees))),
        float(rmse * np.sqrt(degrees / chi2.ppf(0.025, degrees))),
    ]


def proportion_interval(value: float, n: int) -> list[float]:
    half_width = norm.ppf(0.975) * np.sqrt(value * (1.0 - value) / n)
    return [float(max(0.0, value - half_width)), float(min(1.0, value + half_width))]


def metrics(
    score: np.ndarray, opinion: np.ndarray, opinion_ci95: np.ndarray
) -> dict[str, object]:
    predicted = fit_mapping(score, opinion)
    residual = predicted - opinion
    n = len(residual)
    degrees = n - 4
    rmse = float(np.sqrt(np.sum(residual**2) / degrees))
    discounted = np.maximum(0.0, np.abs(residual) - opinion_ci95)
    rmse_star = float(np.sqrt(np.sum(discounted**2) / degrees))
    outlier_ratio = float(np.mean(np.abs(residual) > opinion_ci95))
    plcc = float(np.corrcoef(predicted, opinion)[0, 1])
    srcc = float(np.corrcoef(rankdata(score), rankdata(opinion))[0, 1])
    return {
        "n": n,
        "srcc": srcc,
        "plcc": plcc,
        "plcc_ci95": fisher_interval(plcc, n),
        "rmse": rmse,
        "rmse_ci95": rmse_interval(rmse, n),
        "rmse_star": rmse_star,
        "rmse_star_ci95": rmse_interval(rmse_star, n),
        "outlier_ratio": outlier_ratio,
        "outlier_ratio_ci95": proportion_interval(outlier_ratio, n),
    }


def koniq_ground_truth() -> tuple[dict[str, float], dict[str, float]]:
    frame = pd.read_csv(PROJECT_DIR / "data" / "koniq10k" / "koniq10k_scores.csv")
    counts = frame["c_total"].to_numpy(dtype=float)
    intervals = 1.96 * frame["SD"].to_numpy(dtype=float) / np.sqrt(
        np.maximum(counts, 1)
    )
    return (
        dict(zip(frame["image_name"].astype(str), frame["MOS"].astype(float))),
        dict(zip(frame["image_name"].astype(str), intervals)),
    )


def kadid_ground_truth() -> tuple[dict[str, float], dict[str, float]]:
    frame = pd.read_csv(
        PROJECT_DIR / "data" / "kadid10k" / "kadid10k" / "dmos.csv"
    )
    # KADID-10k reports 30 judgements per distorted image.
    intervals = 1.96 * np.sqrt(np.maximum(frame["var"].to_numpy(dtype=float), 0)) / np.sqrt(30)
    return (
        dict(zip(frame["dist_img"].astype(str), frame["dmos"].astype(float))),
        dict(zip(frame["dist_img"].astype(str), intervals)),
    )


def evaluate_database(
    database: str,
    ground_truth: Callable[[], tuple[dict[str, float], dict[str, float]]],
) -> dict[str, object]:
    opinion, opinion_ci95 = ground_truth()
    output: dict[str, object] = {}
    cache_dir = PROJECT_DIR / "results" / database / "scores_cache"
    for path in sorted(cache_dir.glob("*.csv")):
        frame = pd.read_csv(path)
        score = dict(zip(frame.iloc[:, 0].astype(str), frame.iloc[:, 1].astype(float)))
        keys = [key for key in score if key in opinion and np.isfinite(score[key])]
        if len(keys) < 100:
            continue
        output[path.stem] = metrics(
            np.asarray([score[key] for key in keys]),
            np.asarray([opinion[key] for key in keys]),
            np.asarray([opinion_ci95[key] for key in keys]),
        )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = {
        "koniq10k": evaluate_database("koniq10k", koniq_ground_truth),
        "kadid10k": evaluate_database("kadid10k", kadid_ground_truth),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
