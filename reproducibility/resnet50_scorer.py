"""
ResNet-50 (ImageNet supervised) feature extraction and quality scoring.

Uses Global Average Pooling features (2048-D) from the penultimate layer.
Weights: IMAGENET1K_V2 (improved training recipe from TorchVision).

Scoring: same framework as DINOv2 — mean of per-frame L2 norms (Option A).
This provides a fair CNN baseline for comparison against DINOv2 (ViT).
"""

import gc
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_transform():
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(256, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def load_model(device: str = "cuda") -> nn.Module:
    """Load ResNet-50 with fc replaced by Identity → 2048-D GAP features."""
    model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
    model.fc = nn.Identity()
    model = model.to(device).half().eval()
    return model


def unload_model(model: nn.Module):
    model.cpu()
    del model
    gc.collect()
    torch.cuda.empty_cache()


def preprocess_frames(frames: list[np.ndarray], transform) -> torch.Tensor:
    """BGR uint8 OpenCV frames -> (N, 3, 224, 224) fp16 tensor."""
    tensors = []
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tensors.append(transform(rgb))
    return torch.stack(tensors).half()


def extract_features(
    frames: list[np.ndarray],
    model: nn.Module,
    device: str = "cuda",
    batch_size: int = 32,
) -> np.ndarray:
    """
    Extract GAP features from ResNet-50.

    Args:
        frames: list of BGR uint8 OpenCV frames
        model: ResNet-50 model (fc=Identity, on device, fp16, eval)
        device: cuda or cpu
        batch_size: inference batch size

    Returns:
        np.ndarray of shape (n_frames, 2048) — one vector per frame
    """
    if not frames:
        return np.zeros((0, 2048), dtype=np.float32)

    transform = build_transform()
    batch_tensor = preprocess_frames(frames, transform)
    all_features = []

    for i in range(0, len(frames), batch_size):
        batch = batch_tensor[i:i + batch_size].to(device)
        with torch.inference_mode():
            features = model(batch)  # (B, 2048)
        all_features.append(features.float().cpu().numpy())
        del batch, features

    return np.concatenate(all_features, axis=0)


def score_segment(frame_features: np.ndarray) -> dict:
    """
    Compute quality features from per-frame GAP vectors.

    Same interface as dinov2_scorer.score_segment — returns dict with
    mean_norm, centroid_norm, coherence_R, std_norm.
    """
    if len(frame_features) == 0:
        return {
            "mean_norm": 0.0,
            "centroid_norm": 0.0,
            "coherence_R": 0.0,
            "std_norm": 0.0,
        }

    per_frame_norms = np.linalg.norm(frame_features, axis=1)
    mean_norm = float(per_frame_norms.mean())

    centroid = frame_features.mean(axis=0)
    centroid_norm = float(np.linalg.norm(centroid))

    coherence_R = centroid_norm / (mean_norm + 1e-8)
    std_norm = float(per_frame_norms.std())

    return {
        "mean_norm": mean_norm,
        "centroid_norm": centroid_norm,
        "coherence_R": coherence_R,
        "std_norm": std_norm,
    }


def score_cluster(
    segment_features: dict[str, np.ndarray],
    lambda_val: float = 0.0,
) -> list[tuple[str, float, dict]]:
    """
    Rank segments in a cluster by visual quality.

    Same interface as dinov2_scorer.score_cluster.

    Args:
        segment_features: {segment_id: (n_frames, 2048) array}
        lambda_val: penalty weight for std (0 = pure mean)

    Returns:
        List of (segment_id, quality_score, features_dict) sorted descending.
    """
    scores = []
    for seg_id, feats in segment_features.items():
        s = score_segment(feats)
        quality = s["mean_norm"] - lambda_val * s["std_norm"]
        scores.append((seg_id, quality, s))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores
