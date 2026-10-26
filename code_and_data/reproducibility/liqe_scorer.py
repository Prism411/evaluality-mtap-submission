"""
LIQE — Learned Image Quality Evaluator (Zhang, CVPR 2023).

Multi-task CLIP: predicts quality level (5 categories), distortion type, and scene.
Output is a scalar quality score where higher = better.
Uses pyiqa library: pip install pyiqa
"""

import gc

import cv2
import numpy as np
import torch


def load_model(device: str = "cuda"):
    import pyiqa
    return pyiqa.create_metric("liqe", device=device)


def unload_model(model):
    del model
    gc.collect()
    torch.cuda.empty_cache()


def preprocess_frames(frames: list[np.ndarray]) -> torch.Tensor:
    """BGR uint8 -> (N, 3, H, W) float32 [0, 1]."""
    tensors = []
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        t = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
        tensors.append(t)
    return torch.stack(tensors)


def score_frames(
    frames: list[np.ndarray],
    model,
    device: str = "cuda",
    batch_size: int = 8,
) -> np.ndarray:
    """Per-frame quality scores via LIQE."""
    if not frames:
        return np.zeros(0, dtype=np.float32)

    batch_tensor = preprocess_frames(frames)
    all_scores = []

    for i in range(0, len(frames), batch_size):
        batch = batch_tensor[i:i + batch_size].to(device)
        with torch.inference_mode():
            scores = model(batch)
        all_scores.append(scores.flatten().cpu().numpy())
        del batch, scores

    return np.concatenate(all_scores)


def score_segment(frame_scores: np.ndarray) -> dict:
    if len(frame_scores) == 0:
        return {"mean_score": 0.0, "std_score": 0.0, "min_score": 0.0, "max_score": 0.0}
    return {
        "mean_score": float(frame_scores.mean()),
        "std_score": float(frame_scores.std()),
        "min_score": float(frame_scores.min()),
        "max_score": float(frame_scores.max()),
    }


def score_cluster(
    segment_scores: dict[str, np.ndarray],
) -> list[tuple[str, float, dict]]:
    results = []
    for seg_id, scores in segment_scores.items():
        s = score_segment(scores)
        results.append((seg_id, s["mean_score"], s))
    results.sort(key=lambda x: x[1], reverse=True)
    return results
