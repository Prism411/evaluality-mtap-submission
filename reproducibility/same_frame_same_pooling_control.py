"""Same-frame/same-pooling isolation of SIFT--BoVW versus LIQE.

Each candidate receives the exact same uniformly sampled set of at most 10
1-fps frames.  SIFT--BoVW frame contributions and LIQE frame scores are both
pooled by the arithmetic mean.  Thus frame selection and pooling cannot explain
selection differences inside this fixed-budget control.
"""

from __future__ import annotations

import gc
import json
import os
import time
from collections import Counter
from math import log10
from pathlib import Path

import cv2
import numpy as np
import torch
from sklearn.cluster import KMeans


HERE = Path(__file__).resolve().parent
MANUSCRIPT = Path(
    "/dados/Projetos/memoria-agentes/07-Artigos/"
    "evaluality-webmedia-2026/mtap"
)
DATASET = Path("/dados/Projetos/sumarizador/data/dataset")
OUT = HERE / "same_frame_same_pooling_control.json"
DEPLOYED = json.load(open(MANUSCRIPT / "e2e_sift.json"))
K = 300
CAP = 10
SEED = 42


def save(obj: dict) -> None:
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w") as stream:
        json.dump(obj, stream, indent=1)
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(OUT)


def parse_key(key: str) -> tuple[Path, float, float]:
    topic, stem, start, end = key.split("|")
    return DATASET / topic / f"{stem}.mp4", float(start), float(end)


def frames_for(key: str) -> list[np.ndarray]:
    path, start, end = parse_key(key)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open {path}")
    source_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(source_fps)))
    frames = []
    index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        second = index / source_fps
        if second > end:
            break
        if second >= start and index % step == 0:
            frames.append(frame)
        index += 1
    capture.release()
    if len(frames) > CAP:
        indices = np.linspace(0, len(frames) - 1, CAP).round().astype(int)
        frames = [frames[index] for index in indices]
    if not frames:
        raise RuntimeError(f"no frames decoded for {key}")
    return frames


def sift_descriptors(frames: list[np.ndarray]) -> list[np.ndarray]:
    sift = cv2.SIFT_create()
    output = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, descriptor = sift.detectAndCompute(gray, None)
        output.append(
            descriptor.astype(np.float32, copy=False)
            if descriptor is not None
            else np.empty((0, 128), dtype=np.float32)
        )
    return output


def sift_bovw_mean(per_segment: dict[str, list[np.ndarray]]) -> dict[str, float]:
    concatenated = {
        key: np.concatenate([value for value in values if len(value)], axis=0)
        for key, values in per_segment.items()
    }
    pool = np.concatenate(list(concatenated.values()), axis=0)
    k_eff = min(K, len(pool))
    if k_eff < 2:
        raise RuntimeError("fewer than two descriptors in a cluster")
    model = KMeans(n_clusters=k_eff, random_state=SEED, n_init=1).fit(pool)
    frequencies = {
        key: Counter(model.predict(values)) for key, values in concatenated.items()
    }
    document_frequency = Counter(
        word for values in frequencies.values() for word in values
    )
    output = {}
    for key, values in frequencies.items():
        total = sum(
            count * log10(k_eff / document_frequency[word])
            for word, count in values.items()
        )
        output[key] = float(total / len(per_segment[key]))
    return output


def liqe_mean(metric, frames: list[np.ndarray], device: torch.device) -> float:
    values = []
    with torch.inference_mode():
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = (
                torch.from_numpy(rgb.copy())
                .permute(2, 0, 1)
                .float()
                .div(255)
                .unsqueeze(0)
                .to(device)
            )
            values.append(float(metric(tensor).item()))
    return float(np.mean(values))


def summarize(result: dict) -> None:
    clusters = result["clusters"]
    deployed_changes = sum(
        row["selected"]["liqe_matched_mean"]
        != row["selected"]["published_deployed"]
        for row in clusters.values()
    )
    sift_changes = sum(
        row["selected"]["sift_matched_mean"]
        != row["selected"]["published_deployed"]
        for row in clusters.values()
    )
    disagreements = sum(
        row["selected"]["sift_matched_mean"]
        != row["selected"]["liqe_matched_mean"]
        for row in clusters.values()
    )
    segments = [segment for row in clusters.values() for segment in row["segments"].values()]
    result["summary"] = {
        "n_clusters": len(clusters),
        "sift_liqe_matched_disagreements": disagreements,
        "sift_matched_changes_from_published_deployed": sift_changes,
        "liqe_matched_changes_from_published_deployed": deployed_changes,
        "mean_common_frames": float(np.mean([segment["n_common_frames"] for segment in segments])),
        "segments_at_frame_cap": int(sum(segment["n_common_frames"] == CAP for segment in segments)),
        "segment_slots": len(segments),
    }


def main() -> None:
    import pyiqa

    result = json.load(open(OUT)) if OUT.exists() else {
        "design": {
            "source_sampling": "uniform 1 fps",
            "common_frame_cap": CAP,
            "common_frame_choice": "uniform linspace indices when more than 10 frames",
            "pooling": "arithmetic mean for both scorers",
            "sift_vocabulary": {
                "K": K,
                "idf": "log10(K/document_frequency)",
                "random_state": SEED,
                "n_init": 1,
            },
        },
        "clusters": {},
    }
    device = torch.device("cuda")
    metric = pyiqa.create_metric("liqe", device=device)
    metric.eval()
    started = time.time()
    for number, (cluster, published) in enumerate(DEPLOYED.items(), start=1):
        if cluster in result["clusters"]:
            print(f"[{number}/{len(DEPLOYED)}] skip {cluster}", flush=True)
            continue
        row = {"segments": {}, "scores": {}, "selected": {}}
        descriptors = {}
        for key, values in published.items():
            frames = frames_for(key)
            descriptors[key] = sift_descriptors(frames)
            row["segments"][key] = {
                "n_common_frames": len(frames),
                "n_descriptors": int(sum(len(value) for value in descriptors[key])),
            }
            row["scores"].setdefault("published_deployed", {})[key] = float(values["bovw_sum"])
            row["scores"].setdefault("liqe_matched_mean", {})[key] = liqe_mean(
                metric, frames, device
            )
        row["scores"]["sift_matched_mean"] = sift_bovw_mean(descriptors)
        for field, scores in row["scores"].items():
            row["selected"][field] = max(scores, key=lambda key: scores[key])
        result["clusters"][cluster] = row
        summarize(result)
        save(result)
        print(
            f"[{number}/{len(DEPLOYED)}] {cluster}: "
            f"matched disagreement="
            f"{row['selected']['sift_matched_mean'] != row['selected']['liqe_matched_mean']} "
            f"({(time.time()-started)/60:.1f} min)",
            flush=True,
        )
        gc.collect()
        torch.cuda.empty_cache()
    summarize(result)
    save(result)
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
