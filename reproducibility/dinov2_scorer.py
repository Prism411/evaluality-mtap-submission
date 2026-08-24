"""
DINOv2 ViT-S/14 (with registers) feature extraction and quality scoring.

Uses patch tokens (NOT CLS) because KoLeo regularizer homogenizes CLS norms.
Patch tokens are trained via iBOT masked-image-modeling → sensitive to texture/edges.

Scoring: mean of per-frame L2 norms (Option A, VQA convention).
"""

import gc
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms


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


def load_model(model_name: str = "dinov2_vits14_reg", device: str = "cuda"):
    model = torch.hub.load("facebookresearch/dinov2", model_name)
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


def extract_patch_features(
    frames: list[np.ndarray],
    model: nn.Module,
    device: str = "cuda",
    batch_size: int = 32,
) -> np.ndarray:
    """
    Extract mean-pooled patch token features from DINOv2.

    Args:
        frames: list of BGR uint8 OpenCV frames
        model: DINOv2 model (already on device, fp16, eval)
        device: cuda or cpu
        batch_size: inference batch size

    Returns:
        np.ndarray of shape (n_frames, 384) — one vector per frame
    """
    if not frames:
        return np.zeros((0, 384), dtype=np.float32)

    transform = build_transform()
    batch_tensor = preprocess_frames(frames, transform)
    all_features = []

    for i in range(0, len(frames), batch_size):
        batch = batch_tensor[i:i + batch_size].to(device)
        with torch.inference_mode():
            out = model.forward_features(batch)
            patch_tokens = out["x_norm_patchtokens"]  # (B, 256, 384)
            # Mean spatial pooling: (B, 256, 384) -> (B, 384)
            mean_patches = patch_tokens.mean(dim=1)
        all_features.append(mean_patches.float().cpu().numpy())
        del batch, out, patch_tokens, mean_patches

    return np.concatenate(all_features, axis=0)


def score_segment(frame_features: np.ndarray) -> dict:
    """
    Compute quality features from per-frame patch-token vectors.

    Args:
        frame_features: (N_frames, 384) array

    Returns:
        dict with mean_norm, centroid_norm, coherence_R, std_norm
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

    Args:
        segment_features: {segment_id: (n_frames, 384) array}
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
