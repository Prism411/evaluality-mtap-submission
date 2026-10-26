#!/usr/bin/env python3
"""
Benchmark quality scorers on KONIQ-10k (10,073 real-world images with human MOS).

Computes SRCC and PLCC vs human MOS — the standard IQA evaluation protocol.

Methods tested:
  - QualiCLIP (SOTA NR-IQA, learned)
  - LIQE (multi-task NR-IQA, CVPR 2023)
  - BRISQUE (classic NR-IQA, NSS-based)
  - NIQE (classic NR-IQA, opinion-unaware)
  - Q-Align (LMM-based NR-IQA, 4-bit)
  - DINOv2 (patch token L2 norm — quality proxy, not IQA)
  - ResNet-50 (feature L2 norm — quality proxy, not IQA)
  - KP-density (SIFT keypoint count — handcrafted proxy)
  - SI (Spatial Information, ITU-T P.910 — complexity metric)

Usage:
    cd /data/projects/benchmark
    .venv/bin/python benchmark_koniq.py
    .venv/bin/python benchmark_koniq.py --limit 500          # quick test
    .venv/bin/python benchmark_koniq.py --skip qalign        # skip slow model
    .venv/bin/python benchmark_koniq.py --only qualiclip,dinov2  # run subset
"""

import argparse
import gc
import json
import logging
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr
from scipy.optimize import curve_fit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("benchmark_koniq.log"),
    ],
)
log = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data" / "koniq10k"
SCORES_CSV = DATA_DIR / "koniq10k_scores.csv"
RESULTS_DIR = PROJECT_DIR / "results" / "koniq10k"
CACHE_DIR = RESULTS_DIR / "scores_cache"

# Possible image directories (depends on how zip was extracted)
POSSIBLE_IMAGE_DIRS = [
    DATA_DIR / "512x384",
    DATA_DIR / "koniq10k_512x384",
    DATA_DIR / "images",
    DATA_DIR,
]

ALL_MODELS = [
    "qualiclip", "liqe", "brisque", "niqe", "qalign",
    "dinov2", "resnet50", "kp_density", "si",
    "sift_bovw", "sift_bovw_fixed",
    # CNN+BoVW (SIFT replaced by CNN spatial features, same TF-IDF pipeline)
    "resnet18_bovw", "resnet50_bovw", "resnet101_bovw",
    "vgg16_bovw", "vgg19_bovw",
    "efficientnet_bovw", "efficientnet_b4_bovw",
    "mobilenet_bovw", "mobilenet_v2_bovw",
    "convnext_tiny_bovw", "convnext_small_bovw",
    "densenet121_bovw", "densenet201_bovw",
    "resnext50_bovw", "resnext101_bovw",
    "wide_resnet50_bovw", "wide_resnet101_bovw",
    "inception_v3_bovw", "squeezenet_bovw",
]


# ── Dataset loading ─────────────────────────────────────────────────────

def find_images_dir() -> Path:
    """Find the directory containing KONIQ-10k images."""
    for d in POSSIBLE_IMAGE_DIRS:
        if d.exists() and any(d.glob("*.jpg")):
            return d
    raise FileNotFoundError(
        f"No KONIQ-10k images found. Checked: {[str(d) for d in POSSIBLE_IMAGE_DIRS]}"
    )


def load_dataset(limit: int = 0) -> pd.DataFrame:
    """Load KONIQ-10k metadata with MOS scores."""
    df = pd.read_csv(SCORES_CSV)
    images_dir = find_images_dir()
    log.info(f"Images directory: {images_dir}")

    df["image_path"] = df["image_name"].apply(lambda n: str(images_dir / n))
    existing = df["image_path"].apply(lambda p: Path(p).exists())
    n_found = existing.sum()
    log.info(f"Found {n_found}/{len(df)} images on disk")

    if n_found == 0:
        raise FileNotFoundError("No images found! Check extraction.")

    df = df[existing].reset_index(drop=True)
    if limit > 0:
        df = df.head(limit)
        log.info(f"Limited to {len(df)} images")

    return df


def load_images(paths: list[str]) -> list[np.ndarray]:
    """Load images as BGR numpy arrays."""
    images = []
    for p in paths:
        img = cv2.imread(p)
        if img is None:
            log.warning(f"Failed to load: {p}")
            img = np.zeros((384, 512, 3), dtype=np.uint8)
        images.append(img)
    return images


# ── Caching ─────────────────────────────────────────────────────────────

def save_cache(model_name: str, image_names: list[str], scores: np.ndarray):
    """Save per-image scores for a model."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame({"image_name": image_names, "score": scores})
    out.to_csv(CACHE_DIR / f"{model_name}.csv", index=False)
    log.info(f"  Cached {len(scores)} scores → {CACHE_DIR / f'{model_name}.csv'}")


def load_cache(model_name: str) -> pd.DataFrame | None:
    """Load cached scores if available."""
    path = CACHE_DIR / f"{model_name}.csv"
    if path.exists():
        df = pd.read_csv(path)
        log.info(f"  Loaded {len(df)} cached scores for {model_name}")
        return df
    return None


# ── Scoring functions ───────────────────────────────────────────────────
# Each returns np.ndarray of shape (N,) with one score per image.

OUTER_BATCH = 200  # images loaded into RAM at once


def run_scorer_batched(
    image_paths: list[str],
    score_fn,
    model_name: str,
) -> np.ndarray:
    """Generic batched scorer. score_fn(images) -> np.ndarray of scores."""
    all_scores = []
    n = len(image_paths)
    t0 = time.time()

    for i in range(0, n, OUTER_BATCH):
        batch_paths = image_paths[i:i + OUTER_BATCH]
        batch_images = load_images(batch_paths)
        scores = score_fn(batch_images)
        all_scores.append(scores)
        del batch_images
        elapsed = time.time() - t0
        done = min(i + OUTER_BATCH, n)
        rate = done / elapsed if elapsed > 0 else 0
        eta = (n - done) / rate if rate > 0 else 0
        log.info(f"  {model_name}: {done}/{n} ({rate:.1f} img/s, ETA {eta:.0f}s)")

    return np.concatenate(all_scores)


def score_qualiclip(image_paths: list[str]) -> np.ndarray:
    import qualiclip_scorer
    model = qualiclip_scorer.load_model(device="cuda")

    def fn(images):
        return qualiclip_scorer.score_frames(images, model, device="cuda", batch_size=16)

    scores = run_scorer_batched(image_paths, fn, "qualiclip")
    qualiclip_scorer.unload_model(model)
    return scores


def score_liqe(image_paths: list[str]) -> np.ndarray:
    import liqe_scorer
    model = liqe_scorer.load_model(device="cuda")

    def fn(images):
        return liqe_scorer.score_frames(images, model, device="cuda", batch_size=8)

    scores = run_scorer_batched(image_paths, fn, "liqe")
    liqe_scorer.unload_model(model)
    return scores


def score_brisque(image_paths: list[str]) -> np.ndarray:
    import classic_iqa_scorer
    model = classic_iqa_scorer.load_model("brisque", device="cuda")

    def fn(images):
        return classic_iqa_scorer.score_frames(images, model, device="cuda")

    scores = run_scorer_batched(image_paths, fn, "brisque")
    classic_iqa_scorer.unload_model(model)
    return scores


def score_niqe(image_paths: list[str]) -> np.ndarray:
    import classic_iqa_scorer
    model = classic_iqa_scorer.load_model("niqe", device="cuda")

    def fn(images):
        return classic_iqa_scorer.score_frames(images, model, device="cuda")

    scores = run_scorer_batched(image_paths, fn, "niqe")
    classic_iqa_scorer.unload_model(model)
    return scores


def score_qalign(image_paths: list[str]) -> np.ndarray:
    import qalign_scorer
    model = qalign_scorer.load_model(device="cuda")

    def fn(images):
        return qalign_scorer.score_frames(images, model, device="cuda")

    scores = run_scorer_batched(image_paths, fn, "qalign")
    qalign_scorer.unload_model(model)
    return scores


def score_dinov2(image_paths: list[str]) -> np.ndarray:
    import dinov2_scorer
    model = dinov2_scorer.load_model("dinov2_vits14_reg", device="cuda")

    def fn(images):
        features = dinov2_scorer.extract_patch_features(images, model, device="cuda", batch_size=32)
        return np.linalg.norm(features, axis=1)

    scores = run_scorer_batched(image_paths, fn, "dinov2")
    dinov2_scorer.unload_model(model)
    return scores


def score_resnet50(image_paths: list[str]) -> np.ndarray:
    import resnet50_scorer
    model = resnet50_scorer.load_model(device="cuda")

    def fn(images):
        features = resnet50_scorer.extract_features(images, model, device="cuda", batch_size=32)
        return np.linalg.norm(features, axis=1)

    scores = run_scorer_batched(image_paths, fn, "resnet50")
    resnet50_scorer.unload_model(model)
    return scores


def score_kp_density(image_paths: list[str]) -> np.ndarray:
    sift = cv2.SIFT_create()

    def fn(images):
        counts = []
        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            kps, _ = sift.detectAndCompute(gray, None)
            counts.append(len(kps) if kps is not None else 0)
        return np.array(counts, dtype=np.float32)

    return run_scorer_batched(image_paths, fn, "kp_density")


def score_si(image_paths: list[str]) -> np.ndarray:
    def fn(images):
        si_vals = []
        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float64)
            sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            si_vals.append(np.sqrt(sx**2 + sy**2).std())
        return np.array(si_vals, dtype=np.float32)

    return run_scorer_batched(image_paths, fn, "si")


def score_sift_bovw(image_paths: list[str]) -> np.ndarray:
    """SIFT+BoVW with BUGGY IDF: log10(dict_size / doc_freq).
    Reproduces the original HSMVideoSumm pipeline behavior."""
    from math import log10
    from collections import Counter
    from sklearn.cluster import MiniBatchKMeans

    DICT_SIZE = 300
    sift = cv2.SIFT_create()
    n = len(image_paths)
    t0 = time.time()

    # Phase 1: Extract SIFT descriptors per image
    log.info(f"  sift_bovw: extracting SIFT descriptors from {n} images...")
    all_descriptors_list = []
    per_image_descs = []
    for i, path in enumerate(image_paths):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            per_image_descs.append(None)
            continue
        kps, descs = sift.detectAndCompute(img, None)
        if descs is None or len(descs) == 0:
            per_image_descs.append(None)
        else:
            per_image_descs.append(descs)
            all_descriptors_list.append(descs)
        if (i + 1) % 2000 == 0:
            elapsed = time.time() - t0
            log.info(f"  sift_bovw: extracted {i+1}/{n} ({(i+1)/elapsed:.0f} img/s)")

    log.info(f"  sift_bovw: extraction done, {sum(1 for d in per_image_descs if d is not None)}/{n} images with descriptors")

    if len(all_descriptors_list) < DICT_SIZE:
        log.warning("  sift_bovw: not enough descriptors for K-Means")
        return np.zeros(n, dtype=np.float32)

    # Phase 2: Build vocabulary with MiniBatchKMeans (faster for large N)
    all_descs = np.concatenate(all_descriptors_list)
    log.info(f"  sift_bovw: fitting K-Means on {len(all_descs)} descriptors (k={DICT_SIZE})...")
    kmeans = MiniBatchKMeans(n_clusters=DICT_SIZE, random_state=42, batch_size=10000)
    kmeans.fit(all_descs)
    del all_descs, all_descriptors_list

    # Phase 3: Compute TF-IDF per image (buggy IDF: dict_size as N)
    n_docs = sum(1 for d in per_image_descs if d is not None)
    tfs = []
    for descs in per_image_descs:
        if descs is not None:
            labels = kmeans.predict(descs)
            tfs.append(Counter(labels))
        else:
            tfs.append(None)

    doc_freq = Counter()
    for tf in tfs:
        if tf is not None:
            for word in tf:
                doc_freq[word] += 1

    scores = np.zeros(n, dtype=np.float32)
    for i, tf in enumerate(tfs):
        if tf is None:
            continue
        score = 0.0
        for word, count in tf.items():
            df = doc_freq[word]
            # BUGGY IDF: uses dict_size instead of n_docs
            idf = log10(DICT_SIZE / df) if df > 0 else 0.0
            score += count * idf
        scores[i] = score

    elapsed = time.time() - t0
    log.info(f"  sift_bovw: done in {elapsed:.1f}s")
    return scores


def score_sift_bovw_fixed(image_paths: list[str]) -> np.ndarray:
    """SIFT+BoVW with CORRECTED IDF: log10(n_docs / doc_freq).
    Fixes the IDF formula to use actual document count."""
    from math import log10
    from collections import Counter
    from sklearn.cluster import MiniBatchKMeans

    DICT_SIZE = 300
    sift = cv2.SIFT_create()
    n = len(image_paths)
    t0 = time.time()

    # Phase 1: Extract SIFT descriptors per image
    log.info(f"  sift_bovw_fixed: extracting SIFT descriptors from {n} images...")
    all_descriptors_list = []
    per_image_descs = []
    for i, path in enumerate(image_paths):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            per_image_descs.append(None)
            continue
        kps, descs = sift.detectAndCompute(img, None)
        if descs is None or len(descs) == 0:
            per_image_descs.append(None)
        else:
            per_image_descs.append(descs)
            all_descriptors_list.append(descs)
        if (i + 1) % 2000 == 0:
            elapsed = time.time() - t0
            log.info(f"  sift_bovw_fixed: extracted {i+1}/{n} ({(i+1)/elapsed:.0f} img/s)")

    log.info(f"  sift_bovw_fixed: extraction done, {sum(1 for d in per_image_descs if d is not None)}/{n} images with descriptors")

    if len(all_descriptors_list) < DICT_SIZE:
        log.warning("  sift_bovw_fixed: not enough descriptors for K-Means")
        return np.zeros(n, dtype=np.float32)

    # Phase 2: Build vocabulary
    all_descs = np.concatenate(all_descriptors_list)
    log.info(f"  sift_bovw_fixed: fitting K-Means on {len(all_descs)} descriptors (k={DICT_SIZE})...")
    kmeans = MiniBatchKMeans(n_clusters=DICT_SIZE, random_state=42, batch_size=10000)
    kmeans.fit(all_descs)
    del all_descs, all_descriptors_list

    # Phase 3: Compute TF-IDF per image (CORRECTED IDF: n_docs as N)
    n_docs = sum(1 for d in per_image_descs if d is not None)
    tfs = []
    for descs in per_image_descs:
        if descs is not None:
            labels = kmeans.predict(descs)
            tfs.append(Counter(labels))
        else:
            tfs.append(None)

    doc_freq = Counter()
    for tf in tfs:
        if tf is not None:
            for word in tf:
                doc_freq[word] += 1

    scores = np.zeros(n, dtype=np.float32)
    for i, tf in enumerate(tfs):
        if tf is None:
            continue
        score = 0.0
        for word, count in tf.items():
            df = doc_freq[word]
            # CORRECTED IDF: uses n_docs
            if df >= n_docs:
                idf = 0.0
            else:
                idf = log10(n_docs / df)
            score += count * idf
        scores[i] = score

    elapsed = time.time() - t0
    log.info(f"  sift_bovw_fixed: done in {elapsed:.1f}s")
    return scores


def _make_cnn_bovw_scorer(cnn_name: str):
    """Factory: creates a CNN+BoVW scorer for any CNN from cnn_bovw_scorer.
    Extracts spatial features (H*W descriptors/image), then BoVW+TF-IDF (corrected IDF)."""

    def scorer(image_paths: list[str]) -> np.ndarray:
        import torch
        import torch.nn as nn
        from torchvision import transforms
        from math import log10
        from collections import Counter
        from sklearn.cluster import MiniBatchKMeans

        DICT_SIZE = 300
        BATCH_SIZE = 32
        method = f"{cnn_name}_bovw"
        n = len(image_paths)
        t0 = time.time()

        # Load CNN spatial feature extractor
        import cnn_bovw_scorer as cbs
        model = cbs.load_model(cnn_name, device="cuda")
        transform = cbs.build_transform()

        # Phase 1: Extract CNN spatial features per image
        log.info(f"  {method}: extracting spatial features from {n} images...")
        per_image_descs = []
        all_descriptors_list = []

        for i in range(0, n, BATCH_SIZE):
            batch_paths = image_paths[i:i + BATCH_SIZE]
            tensors = []
            valid_indices = []
            for j, path in enumerate(batch_paths):
                img = cv2.imread(path)
                if img is None:
                    continue
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                tensors.append(transform(rgb))
                valid_indices.append(j)

            if not tensors:
                for _ in batch_paths:
                    per_image_descs.append(None)
                continue

            batch = torch.stack(tensors).to("cuda").half()
            with torch.inference_mode():
                spatial = model(batch)  # (B, C, H, W)
                B, C, H, W = spatial.shape
                descs = spatial.float().permute(0, 2, 3, 1).reshape(B, H * W, C)
                descs = torch.nn.functional.normalize(descs, p=2, dim=2)
                descs_np = descs.cpu().numpy()
            del batch, spatial, descs

            # Map back to original indices
            desc_idx = 0
            for j in range(len(batch_paths)):
                if desc_idx < len(valid_indices) and valid_indices[desc_idx] == j:
                    d = descs_np[desc_idx]
                    per_image_descs.append(d)
                    all_descriptors_list.append(d)
                    desc_idx += 1
                else:
                    per_image_descs.append(None)

            done = min(i + BATCH_SIZE, n)
            if done % 2000 < BATCH_SIZE:
                elapsed = time.time() - t0
                log.info(f"  {method}: {done}/{n} ({done/elapsed:.0f} img/s)")

        n_valid = sum(1 for d in per_image_descs if d is not None)
        log.info(f"  {method}: extraction done, {n_valid}/{n} images with descriptors")

        # Unload CNN
        cbs.unload_model(model)

        total_descs = sum(len(d) for d in all_descriptors_list)
        if total_descs < DICT_SIZE:
            log.warning(f"  {method}: not enough descriptors ({total_descs}) for K-Means (k={DICT_SIZE})")
            return np.zeros(n, dtype=np.float32)

        # Phase 2: Build vocabulary
        all_descs = np.concatenate(all_descriptors_list)
        log.info(f"  {method}: fitting K-Means on {len(all_descs)} descriptors (k={DICT_SIZE})...")
        kmeans = MiniBatchKMeans(n_clusters=DICT_SIZE, random_state=42, batch_size=10000)
        kmeans.fit(all_descs)
        del all_descs, all_descriptors_list

        # Phase 3: TF-IDF (corrected IDF: n_docs/df)
        n_docs = n_valid
        tfs = []
        for descs in per_image_descs:
            if descs is not None:
                labels = kmeans.predict(descs)
                tfs.append(Counter(labels))
            else:
                tfs.append(None)

        doc_freq = Counter()
        for tf in tfs:
            if tf is not None:
                for word in tf:
                    doc_freq[word] += 1

        scores = np.zeros(n, dtype=np.float32)
        for idx, tf in enumerate(tfs):
            if tf is None:
                continue
            score = 0.0
            for word, count in tf.items():
                df = doc_freq[word]
                if df >= n_docs:
                    idf = 0.0
                else:
                    idf = log10(n_docs / df)
                score += count * idf
            scores[idx] = score

        elapsed = time.time() - t0
        log.info(f"  {method}: done in {elapsed:.1f}s")
        return scores

    return scorer


# CNN+BoVW: map benchmark name → cnn_bovw_scorer model name
# All get "_bovw" suffix to avoid collision with existing methods (e.g. resnet50)
_CNN_BOVW_MAP = {
    "resnet18_bovw": "resnet18",
    "resnet50_bovw": "resnet50",
    "resnet101_bovw": "resnet101",
    "vgg16_bovw": "vgg16",
    "vgg19_bovw": "vgg19",
    "efficientnet_bovw": "efficientnet",
    "efficientnet_b4_bovw": "efficientnet_b4",
    "mobilenet_bovw": "mobilenet",
    "mobilenet_v2_bovw": "mobilenet_v2",
    "convnext_tiny_bovw": "convnext_tiny",
    "convnext_small_bovw": "convnext_small",
    "densenet121_bovw": "densenet121",
    "densenet201_bovw": "densenet201",
    "resnext50_bovw": "resnext50",
    "resnext101_bovw": "resnext101",
    "wide_resnet50_bovw": "wide_resnet50",
    "wide_resnet101_bovw": "wide_resnet101",
    "inception_v3_bovw": "inception_v3",
    "squeezenet_bovw": "squeezenet",
}

_CNN_BOVW_SCORERS = {
    bench_name: _make_cnn_bovw_scorer(cnn_name)
    for bench_name, cnn_name in _CNN_BOVW_MAP.items()
}

SCORER_MAP = {
    "qualiclip": score_qualiclip,
    "liqe": score_liqe,
    "brisque": score_brisque,
    "niqe": score_niqe,
    "qalign": score_qalign,
    "dinov2": score_dinov2,
    "resnet50": score_resnet50,
    "kp_density": score_kp_density,
    "si": score_si,
    "sift_bovw": score_sift_bovw,
    "sift_bovw_fixed": score_sift_bovw_fixed,
    **_CNN_BOVW_SCORERS,
}

# Higher = better quality for these methods (positive SRCC expected with MOS)
HIGHER_IS_BETTER = {
    "qualiclip", "liqe", "qalign", "dinov2", "resnet50", "kp_density", "si",
    "sift_bovw", "sift_bovw_fixed",
} | set(_CNN_BOVW_SCORERS.keys())
# Lower = better quality for these (negative SRCC expected with MOS)
LOWER_IS_BETTER = {"brisque", "niqe"}


# ── Metrics ─────────────────────────────────────────────────────────────

def logistic_fit(x, a, b, c, d):
    """4-parameter logistic function for nonlinear mapping before PLCC."""
    return a / (1 + np.exp(-c * (x - d))) + b


def compute_metrics(predicted: np.ndarray, mos: np.ndarray) -> dict:
    """Compute SRCC, PLCC, and PLCC after logistic fit (standard IQA protocol)."""
    # Remove NaN/Inf
    mask = np.isfinite(predicted) & np.isfinite(mos)
    pred = predicted[mask]
    gt = mos[mask]

    if len(pred) < 10:
        return {"srcc": 0.0, "plcc": 0.0, "plcc_fitted": 0.0, "n": len(pred)}

    # SRCC (Spearman Rank Correlation Coefficient)
    srcc, srcc_p = spearmanr(pred, gt)

    # PLCC (Pearson Linear Correlation Coefficient)
    plcc, plcc_p = pearsonr(pred, gt)

    # PLCC after 4-parameter logistic fit (standard nonlinear mapping)
    plcc_fitted = plcc  # fallback
    try:
        p0 = [gt.max() - gt.min(), gt.min(), 1.0, np.median(pred)]
        popt, _ = curve_fit(logistic_fit, pred, gt, p0=p0, maxfev=5000)
        pred_fitted = logistic_fit(pred, *popt)
        plcc_fitted, _ = pearsonr(pred_fitted, gt)
    except Exception:
        pass

    return {
        "srcc": float(srcc),
        "srcc_p": float(srcc_p),
        "plcc": float(plcc),
        "plcc_fitted": float(plcc_fitted),
        "n": int(len(pred)),
    }


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="KONIQ-10k quality benchmark")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of images (0=all)")
    parser.add_argument("--skip", type=str, default="", help="Comma-separated models to skip")
    parser.add_argument("--only", type=str, default="", help="Comma-separated models to run (overrides skip)")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cached scores")
    args = parser.parse_args()

    # Determine which models to run
    if args.only:
        models = [m.strip() for m in args.only.split(",")]
    else:
        skip = set(m.strip() for m in args.skip.split(",") if m.strip())
        models = [m for m in ALL_MODELS if m not in skip]

    log.info(f"Models to benchmark: {models}")

    # Load dataset
    df = load_dataset(limit=args.limit)
    image_paths = df["image_path"].tolist()
    image_names = df["image_name"].tolist()
    mos = df["MOS"].values

    log.info(f"Dataset: {len(df)} images, MOS range [{mos.min():.1f}, {mos.max():.1f}]")

    # Run each model
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for model_name in models:
        log.info(f"\n{'='*60}")
        log.info(f"Running: {model_name}")
        log.info(f"{'='*60}")

        # Check cache
        if not args.no_cache:
            cached = load_cache(model_name)
            if cached is not None and len(cached) == len(df):
                # Verify same images
                if list(cached["image_name"]) == image_names:
                    scores = cached["score"].values
                    metrics = compute_metrics(scores, mos)
                    results[model_name] = metrics
                    log.info(f"  → SRCC={metrics['srcc']:.4f}  PLCC={metrics['plcc_fitted']:.4f} (cached)")
                    continue

        # Run scorer
        t0 = time.time()
        try:
            scorer_fn = SCORER_MAP[model_name]
            scores = scorer_fn(image_paths)
        except Exception as e:
            log.error(f"  FAILED: {e}")
            results[model_name] = {"error": str(e)}
            continue

        elapsed = time.time() - t0
        log.info(f"  Completed in {elapsed:.1f}s ({len(scores)/elapsed:.1f} img/s)")

        # Cache scores
        save_cache(model_name, image_names, scores)

        # Compute metrics
        metrics = compute_metrics(scores, mos)
        metrics["time_s"] = round(elapsed, 1)
        results[model_name] = metrics

        direction = "↑" if model_name in HIGHER_IS_BETTER else "↓"
        log.info(f"  → SRCC={metrics['srcc']:.4f}  PLCC={metrics['plcc_fitted']:.4f}  ({direction} is better)")

        # Force cleanup
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass

    # ── Summary ──────────────────────────────────────────────────────

    # Save full results JSON
    with open(RESULTS_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"\nResults saved to {RESULTS_DIR / 'results.json'}")

    # Print summary table
    print("\n" + "=" * 75)
    print("KONIQ-10k Benchmark Results")
    print(f"Images: {len(df)} | MOS range: [{mos.min():.1f}, {mos.max():.1f}]")
    print("=" * 75)
    print(f"{'Method':<14} {'Type':<12} {'SRCC':>8} {'PLCC':>8} {'PLCC*':>8} {'Time':>8}")
    print("-" * 75)

    type_map = {
        "qualiclip": "IQA (NR)",
        "liqe": "IQA (NR)",
        "brisque": "IQA (NR)",
        "niqe": "IQA (NR)",
        "qalign": "IQA (LMM)",
        "dinov2": "Proxy",
        "resnet50": "Proxy",
        "kp_density": "Handcraft",
        "si": "Complexity",
        "sift_bovw": "BoVW",
        "sift_bovw_fixed": "BoVW",
    }
    # Add CNN+BoVW types dynamically
    for m in ALL_MODELS:
        if m.endswith("_bovw") and m not in type_map:
            type_map[m] = "CNN+BoVW"

    for model_name in ALL_MODELS:
        if model_name not in results:
            continue
        r = results[model_name]
        if "error" in r:
            print(f"{model_name:<14} {'—':<12} {'ERROR':>8} {'':>8} {'':>8} {'':>8}")
            continue

        mtype = type_map.get(model_name, "?")
        srcc = abs(r["srcc"])
        plcc = abs(r["plcc"])
        plcc_f = abs(r["plcc_fitted"])
        time_s = r.get("time_s", "—")
        time_str = f"{time_s}s" if isinstance(time_s, (int, float)) else time_s
        print(f"{model_name:<14} {mtype:<12} {srcc:>8.4f} {plcc:>8.4f} {plcc_f:>8.4f} {time_str:>8}")

    print("-" * 75)
    print("SRCC = Spearman Rank Correlation | PLCC = Pearson Linear Correlation")
    print("PLCC* = PLCC after 4-param logistic fit (standard IQA protocol)")
    print("All values are |absolute|. Higher = better correlation with human MOS.")


if __name__ == "__main__":
    main()
