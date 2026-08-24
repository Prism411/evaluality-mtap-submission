"""
QualiCLIP — learned No-Reference Image Quality Assessment (Agnolucci 2024).

Unlike DINOv2/ResNet-50 (which use L2 norm as quality PROXY), QualiCLIP is
an actual trained quality predictor. It outputs a scalar quality score per frame
in [0, 1] where higher = better quality.

Uses pyiqa library: pip install pyiqa
"""

import gc

import cv2
import numpy as np
import torch
import torch.nn as nn


def load_model(device: str = "cuda"):
    """Load QualiCLIP via pyiqa. Returns the inference model."""
    import pyiqa
    model = pyiqa.create_metric("qualiclip", device=device)
    return model


def unload_model(model):
    del model
    gc.collect()
    torch.cuda.empty_cache()


def preprocess_frames(frames: list[np.ndarray]) -> torch.Tensor:
    """BGR uint8 OpenCV frames -> (N, 3, H, W) float32 tensor in [0, 1].

    QualiCLIP handles its own resizing/normalization internally.
    We just need to convert BGR->RGB and scale to [0, 1].
    """
    tensors = []
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # HWC uint8 -> CHW float32 [0, 1]
        t = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
        tensors.append(t)
    return torch.stack(tensors)


def score_frames(
    frames: list[np.ndarray],
    model,
    device: str = "cuda",
    batch_size: int = 16,
) -> np.ndarray:
    """
    Compute per-frame quality scores using QualiCLIP.

    Args:
        frames: list of BGR uint8 OpenCV frames
        model: pyiqa QualiCLIP model
        device: cuda or cpu
        batch_size: inference batch size (smaller than DINOv2 — CLIP is heavier)

    Returns:
        np.ndarray of shape (n_frames,) — quality score per frame in [0, 1]
    """
    if not frames:
        return np.zeros(0, dtype=np.float32)

    batch_tensor = preprocess_frames(frames)
    all_scores = []

    for i in range(0, len(frames), batch_size):
        batch = batch_tensor[i:i + batch_size].to(device)
        with torch.inference_mode():
            scores = model(batch)  # (B, 1) or (B,)
        all_scores.append(scores.flatten().cpu().numpy())
        del batch, scores

    return np.concatenate(all_scores)


def score_segment(frame_scores: np.ndarray) -> dict:
    """
    Compute segment-level quality features from per-frame scores.

    Args:
        frame_scores: (N_frames,) array of per-frame quality scores

    Returns:
        dict with mean_score, std_score, min_score, max_score, median_score
    """
    if len(frame_scores) == 0:
        return {
            "mean_score": 0.0,
            "std_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "median_score": 0.0,
        }

    return {
        "mean_score": float(frame_scores.mean()),
        "std_score": float(frame_scores.std()),
        "min_score": float(frame_scores.min()),
        "max_score": float(frame_scores.max()),
        "median_score": float(np.median(frame_scores)),
    }


def score_cluster(
    segment_scores: dict[str, np.ndarray],
) -> list[tuple[str, float, dict]]:
    """
    Rank segments in a cluster by QualiCLIP quality.

    Args:
        segment_scores: {segment_id: (n_frames,) per-frame scores}

    Returns:
        List of (segment_id, mean_quality, features_dict) sorted descending.
    """
    results = []
    for seg_id, scores in segment_scores.items():
        s = score_segment(scores)
        results.append((seg_id, s["mean_score"], s))
    results.sort(key=lambda x: x[1], reverse=True)
    return results
