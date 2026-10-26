"""
Classic NR-IQA metrics: BRISQUE and NIQE.

These are expected to show CEILING EFFECT on professional broadcast content
(scores clustered in a narrow range with minimal discrimination).
Documenting this failure is itself a publishable finding.

BRISQUE: Mittal et al. (2012) — NSS features + SVR, trained on LIVE IQA (synthetic distortions)
NIQE: Mittal et al. (2013) — NSS features, no training labels needed

Both: LOWER score = BETTER quality (opposite of QualiCLIP/LIQE).
"""

import gc

import cv2
import numpy as np
import torch


def load_model(metric_name: str, device: str = "cuda"):
    """Load BRISQUE or NIQE via pyiqa.

    Args:
        metric_name: 'brisque' or 'niqe'
    """
    import pyiqa
    return pyiqa.create_metric(metric_name, device=device)


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
) -> np.ndarray:
    """Per-frame quality scores. NOTE: processed one at a time (BRISQUE/NIQE
    operate on single images, not batches)."""
    if not frames:
        return np.zeros(0, dtype=np.float32)

    batch_tensor = preprocess_frames(frames)
    all_scores = []

    for i in range(len(frames)):
        frame_t = batch_tensor[i:i+1].to(device)
        with torch.inference_mode():
            score = model(frame_t)
        all_scores.append(score.item())
        del frame_t, score

    return np.array(all_scores, dtype=np.float32)


def score_segment(frame_scores: np.ndarray, lower_better: bool = True) -> dict:
    if len(frame_scores) == 0:
        return {"mean_score": 0.0, "std_score": 0.0, "min_score": 0.0,
                "max_score": 0.0, "iqr": 0.0, "lower_better": lower_better}

    q25, q75 = np.percentile(frame_scores, [25, 75])
    return {
        "mean_score": float(frame_scores.mean()),
        "std_score": float(frame_scores.std()),
        "min_score": float(frame_scores.min()),
        "max_score": float(frame_scores.max()),
        "iqr": float(q75 - q25),
        "lower_better": lower_better,
    }


def score_cluster(
    segment_scores: dict[str, np.ndarray],
    lower_better: bool = True,
) -> list[tuple[str, float, dict]]:
    """Rank segments. For BRISQUE/NIQE, lower = better, so sort ascending."""
    results = []
    for seg_id, scores in segment_scores.items():
        s = score_segment(scores, lower_better)
        results.append((seg_id, s["mean_score"], s))
    results.sort(key=lambda x: x[1], reverse=not lower_better)
    return results
