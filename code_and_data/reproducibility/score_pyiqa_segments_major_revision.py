#!/usr/bin/env python3
"""Complete missing pyiqa scores on the common 42-cluster segment set.

The sampler reproduces the original evaluation harness: source-frame indices
divisible by round(source_fps) are retained when their timestamps fall inside the
segment. Results are written to a new JSON so the original measurement file is
never overwritten.
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

import cv2
import numpy as np
import pyiqa
import torch


MANUSCRIPT = Path(
    "/data/projects/workspace/07-Artigos/"
    "earlier-workspace/venue"
)
CLUSTERS = MANUSCRIPT / "e2e_sift.json"
EXISTING = MANUSCRIPT / "e2e_scores.json"
OUTPUT = MANUSCRIPT / "e2e_scores_major_revision.json"
DATASET = Path("/data/projects/platform/data/dataset")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+", help="pyiqa registry names")
    parser.add_argument(
        "--output-keys",
        nargs="+",
        help="JSON keys; defaults to the model names",
    )
    return parser.parse_args()


def segments() -> dict[str, tuple[Path, float, float]]:
    clusters = json.loads(CLUSTERS.read_text())
    result: dict[str, tuple[Path, float, float]] = {}
    for members in clusters.values():
        for segment in members:
            topic, stem, start, end = segment.split("|")
            result[segment] = (
                DATASET / topic / f"{stem}.mp4",
                float(start),
                float(end),
            )
    missing = [str(path) for path, _, _ in result.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing source videos: {missing[:3]}")
    return result


def sample_frames(path: Path, start: float, end: float) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return []
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(source_fps)))
    first = int(np.ceil(start * source_fps / step)) * step
    last = int(np.floor(end * source_fps / step)) * step
    frames: list[np.ndarray] = []
    for index in range(first, last + 1, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
    cap.release()
    return frames


def score_segment(metric: torch.nn.Module, frames: list[np.ndarray]) -> float | None:
    values: list[float] = []
    with torch.inference_mode():
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = (
                torch.from_numpy(rgb.copy())
                .permute(2, 0, 1)
                .float()
                .div(255)
                .unsqueeze(0)
                .cuda(non_blocking=True)
            )
            values.append(float(metric(tensor).detach().cpu().reshape(-1)[0]))
    return float(np.mean(values)) if values else None


def main() -> None:
    args = parse_args()
    output_keys = args.output_keys or args.models
    if len(output_keys) != len(args.models):
        raise ValueError("--output-keys must have the same length as models")

    scores = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else json.loads(EXISTING.read_text())
    segment_map = segments()
    for model_name, output_key in zip(args.models, output_keys, strict=True):
        if output_key in scores and all(
            scores[output_key].get(segment) is not None for segment in segment_map
        ):
            print(f"complete: {output_key}", flush=True)
            continue
        metric = pyiqa.create_metric(model_name, device="cuda")
        per_segment: dict[str, float | None] = {}
        for number, (segment, (path, start, end)) in enumerate(segment_map.items(), 1):
            per_segment[segment] = score_segment(
                metric, sample_frames(path, start, end)
            )
            if number % 10 == 0:
                print(f"{output_key}: {number}/{len(segment_map)}", flush=True)
        scores[output_key] = per_segment
        OUTPUT.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")
        print(f"wrote {output_key}: {len(per_segment)} segments", flush=True)
        del metric
        gc.collect()
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
