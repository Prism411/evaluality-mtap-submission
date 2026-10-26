"""Validate the exact DOVER technical output on the 800 constructed pairs.

The 20-segment subset, 1-fps sampling, 30-frame cap, degradation functions and
levels match the published constructed experiment.  Each image sequence is
wrapped in the same MP4 codec before DOVER inference; the H.264 condition first
passes through the declared CRF degradation and then through that common
wrapper.  The official DOVER technical branch is evaluated with paired random
fragment locations (seed 42 for every condition).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
from scipy.stats import spearmanr

from dover_technical_runtime import DoverTechnical


HERE = Path(__file__).resolve().parent
MANUSCRIPT = Path(
    "/data/projects/workspace/07-Artigos/"
    "earlier-workspace/venue"
)
DATASET = Path("/data/projects/platform/data/dataset")
SUBSET_SOURCE = MANUSCRIPT / "derived_data" / "synth_sift.json"
OUT = HERE / "dover_constructed_pairs.json"
CAP = 30
LEVELS = 5
SEED = 42


def atomic_json(obj: dict) -> None:
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    tmp.replace(OUT)


def parse_tag(tag: str) -> tuple[Path, float, float]:
    topic, stem, interval = tag.split("__")
    start, end = interval.split("_", 1)
    return DATASET / topic / f"{stem}.mp4", float(start), float(end)


def sample_frames(tag: str) -> list[np.ndarray]:
    path, start, end = parse_tag(tag)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(source_fps)))
    frames = []
    index = 0
    while True:
        ok, image = cap.read()
        if not ok:
            break
        second = index / source_fps
        if second > end:
            break
        if second >= start and index % step == 0:
            frames.append(image)
        index += 1
    cap.release()
    if len(frames) > CAP:
        indices = np.linspace(0, len(frames) - 1, CAP).round().astype(int)
        frames = [frames[index] for index in indices]
    if not frames:
        raise RuntimeError(f"no frames decoded for {tag}")
    return frames


def blur(image, level):
    kernel = [3, 5, 9, 15, 23][level - 1]
    return cv2.GaussianBlur(image, (kernel, kernel), 0)


def noise(image, level):
    sigma = [5, 12, 22, 35, 50][level - 1]
    values = np.random.default_rng(1000 + level).normal(0, sigma, image.shape)
    return np.clip(image.astype(np.float32) + values, 0, 255).astype(np.uint8)


def dark(image, level):
    factor = [0.80, 0.62, 0.46, 0.32, 0.20][level - 1]
    return np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def jpeg(image, level):
    quality = [40, 25, 15, 9, 5][level - 1]
    ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.imdecode(buffer, cv2.IMREAD_COLOR) if ok else image


def rescale(image, level):
    factor = [0.75, 0.55, 0.40, 0.28, 0.18][level - 1]
    height, width = image.shape[:2]
    small = cv2.resize(
        image,
        (max(2, int(width * factor)), max(2, int(height * factor))),
        interpolation=cv2.INTER_AREA,
    )
    return cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR)


def motion(image, level):
    kernel_size = [5, 9, 15, 23, 33][level - 1]
    kernel = np.zeros((kernel_size, kernel_size), np.float32)
    kernel[kernel_size // 2, :] = 1.0 / kernel_size
    return cv2.filter2D(image, -1, kernel)


def satur(image, level):
    factor = [0.75, 0.55, 0.35, 0.18, 0.05][level - 1]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] *= factor
    return cv2.cvtColor(
        np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR
    )


SPATIAL = {
    "blur": blur,
    "noise": noise,
    "dark": dark,
    "jpeg": jpeg,
    "rescale": rescale,
    "motion": motion,
    "satur": satur,
}
CRF = [30, 36, 41, 45, 50]


def write_video(frames: list[np.ndarray], path: Path, fps: float = 5.0) -> None:
    height, width = frames[0].shape[:2]
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        raise RuntimeError(f"cannot create {path}")
    for frame in frames:
        writer.write(frame)
    writer.release()


def h264(frames: list[np.ndarray], level: int, directory: Path) -> list[np.ndarray]:
    source = directory / "h264_source.mp4"
    degraded = directory / "h264_degraded.mp4"
    write_video(frames, source)
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-c:v", "libx264", "-crf", str(CRF[level - 1]),
            "-preset", "veryfast", str(degraded),
        ],
        check=True,
    )
    capture = cv2.VideoCapture(str(degraded))
    output = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        output.append(frame)
    capture.release()
    return output if len(output) == len(frames) else frames


def bootstrap_accuracy(rows: list[dict], seed: int = SEED, repetitions: int = 10000) -> list[float]:
    segments = sorted({row["segment"] for row in rows})
    by_segment = {segment: [row for row in rows if row["segment"] == segment] for segment in segments}
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(repetitions):
        draw = rng.choice(segments, size=len(segments), replace=True)
        sample = [row for segment in draw for row in by_segment[segment]]
        estimates.append(100 * np.mean([row["correct"] for row in sample]))
    return [float(x) for x in np.percentile(estimates, [2.5, 97.5])]


def summarize(result: dict) -> None:
    rows = []
    by_type = {name: [] for name in [*SPATIAL, "h264"]}
    monotonicity = {name: [] for name in by_type}
    for segment, values in result["segments"].items():
        original = values["original"]
        for dtype in by_type:
            levels = []
            for level in range(1, LEVELS + 1):
                degraded = values["conditions"][f"{dtype}_{level}"]
                row = {
                    "segment": segment,
                    "type": dtype,
                    "level": level,
                    "original": original,
                    "degraded": degraded,
                    "correct": original > degraded,
                    "tie": original == degraded,
                }
                rows.append(row)
                by_type[dtype].append(row)
                levels.append(degraded)
            rho = spearmanr(range(1, LEVELS + 1), levels).statistic
            monotonicity[dtype].append(float(-rho))

    def stats(items: list[dict]) -> dict:
        return {
            "n_pairs": len(items),
            "accuracy_percent": float(100 * np.mean([row["correct"] for row in items])),
            "ties": int(sum(row["tie"] for row in items)),
            "segment_block_ci95": bootstrap_accuracy(items),
        }

    summary = stats(rows)
    summary["by_type"] = {}
    for dtype, items in by_type.items():
        summary["by_type"][dtype] = stats(items)
        summary["by_type"][dtype]["mean_direction_aligned_severity_srcc"] = float(
            np.mean(monotonicity[dtype])
        )
    restricted = [row for row in rows if row["type"] not in {"dark", "satur"}]
    summary["excluding_darkening_and_desaturation"] = stats(restricted)
    result["summary"] = summary


def main() -> None:
    source = json.load(open(SUBSET_SOURCE))
    subset = source["_subset"]
    result = json.load(open(OUT)) if OUT.exists() else {
        "configuration": {
            "model": "official DOVER technical branch",
            "checkpoint": "DOVER.pth",
            "checkpoint_sha256": "f4a42c0bbc94c94dd7409e7f40887d44c5c30314d1d09e7edf03cc35813b4838",
            "config": "dover.yml val-l1080p technical sample type",
            "device": "cuda",
            "paired_fragment_seed": SEED,
            "sequence_wrapper": "MP4V, 5 fps, identical for original and degraded",
            "n_segments": len(subset),
            "conditions_per_segment": 41,
        },
        "segments": {},
    }
    scorer = DoverTechnical(device="cuda", seed=SEED)
    started = time.time()
    for index, segment in enumerate(subset, start=1):
        current = result["segments"].setdefault(segment, {"conditions": {}})
        frames = sample_frames(segment)
        with tempfile.TemporaryDirectory(prefix="dover-pair-") as directory_name:
            directory = Path(directory_name)
            if "original" not in current:
                video = directory / "condition.mp4"
                write_video(frames, video)
                current["original"] = scorer.score(video)
                atomic_json(result)
            for dtype in [*SPATIAL, "h264"]:
                for level in range(1, LEVELS + 1):
                    condition = f"{dtype}_{level}"
                    if condition in current["conditions"]:
                        continue
                    if dtype == "h264":
                        altered = h264(frames, level, directory)
                    else:
                        altered = [SPATIAL[dtype](frame, level) for frame in frames]
                    video = directory / "condition.mp4"
                    write_video(altered, video)
                    current["conditions"][condition] = scorer.score(video)
                    atomic_json(result)
                    print(
                        f"[{index}/{len(subset)}] {segment[:34]:<34} {condition:<10} "
                        f"{(time.time()-started)/60:.1f} min",
                        flush=True,
                    )
        summarize(result)
        atomic_json(result)
    summarize(result)
    atomic_json(result)
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
