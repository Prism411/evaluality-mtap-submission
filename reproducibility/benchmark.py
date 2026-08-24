#!/usr/bin/env python3
"""
Benchmark: SIFT+BoVW vs DINOv2 for visual quality scoring in HSMVideoSumm Stage 4.

Runs both methods on the same redundancy clusters and compares results.
Does NOT modify the open-video-summary library.

Usage:
    cd /dados/Projetos/quality-benchmark
    .venv/bin/python benchmark.py
"""

import sys
import json
import time
import copy
import logging
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import h5py
from scipy.stats import kendalltau, spearmanr

# Add open-video-summary to path (read-only import)
sys.path.insert(0, "/dados/MESTRADO-USP/open-video-summary")

from open_video_summary.handlers.summary import SummarySegmentHandler
from open_video_summary.core.selection_criteria.redundancy import ContentBasedRedundancy
from open_video_summary.core.selection_criteria.quality import QualityPick
from open_video_summary.utils.processing.video import VideoProcessor
from open_video_summary.utils.processing.image import ImageProcessor, BagOfVisualWords
from open_video_summary.parsers.video import VideoLoader
from open_video_summary.entities.video import Video, VideoSegment

import dinov2_scorer
import resnet50_scorer
import qualiclip_scorer
import liqe_scorer
import classic_iqa_scorer
import cnn_bovw_scorer
import si_ti_scorer
import qalign_scorer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent
RESULTS_DIR = PROJECT_DIR / "results"
CACHE_DIR = PROJECT_DIR / "cache"


# ── Segment identification ────────────────────────────────────────────

def seg_id(seg: VideoSegment) -> str:
    """Unique string ID for a segment (video_name:start-end)."""
    video_name = Path(seg.video_path).stem
    return f"{video_name}:{seg.start:.1f}-{seg.end:.1f}"


# ── SIFT feature extraction (shared by both IDF variants) ─────────────

def extract_sift_features(cluster: set[VideoSegment]) -> dict[VideoSegment, np.ndarray]:
    """Extract SIFT keyframe descriptors for each segment in a cluster."""
    seg_features = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=True,
            start_second=segment.start, end_second=segment.end,
        )
        if len(frames) < 3:
            continue
        try:
            features = ImageProcessor.ks_sift(frames)
            seg_features[segment] = features
        except Exception as e:
            log.warning(f"SIFT failed for {seg_id(segment)}: {e}")
            continue
    return seg_features


# ── SIFT+BoVW scoring (original buggy IDF: dict_size as N) ───────────

def run_sift_scoring_buggy(
    cluster: set[VideoSegment],
    seg_features: dict[VideoSegment, np.ndarray],
    bovw_dict_size: int = 300,
) -> list[tuple[str, float]]:
    """
    SIFT+BoVW with ORIGINAL (buggy) IDF: log10(dict_size / doc_freq).
    Hardcoded here to preserve the old behavior for comparison,
    since the library's BagOfVisualWords has been fixed.
    """
    from math import log10
    from collections import Counter

    if len(seg_features) < 2:
        return [(seg_id(seg), 0.0) for seg in cluster]

    from sklearn.cluster import KMeans
    all_descriptors = np.concatenate(list(seg_features.values()))
    kmeans = KMeans(n_clusters=bovw_dict_size, random_state=42)
    kmeans.fit(all_descriptors)

    tfs = {}
    for segment, descriptors in seg_features.items():
        labels = kmeans.predict(descriptors)
        tfs[segment] = Counter(labels)

    doc_freq = Counter(key for counts in tfs.values() for key in counts.keys())

    # BUGGY IDF: uses dict_size (300) instead of N_docs
    results = []
    for segment, tf_counts in tfs.items():
        score = 0.0
        for word, tf in tf_counts.items():
            df = doc_freq[word]
            idf = log10(bovw_dict_size / df)
            score += tf * idf
        results.append((seg_id(segment), score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── SIFT+BoVW scoring (corrected IDF: N_docs as N) ───────────────────

def run_sift_scoring_corrected(
    cluster: set[VideoSegment],
    seg_features: dict[VideoSegment, np.ndarray],
    bovw_dict_size: int = 300,
) -> list[tuple[str, float]]:
    """
    SIFT+BoVW with CORRECTED IDF: log10(N_docs / doc_freq).
    Re-implements TF-IDF with the correct formula.
    """
    from math import log10
    from collections import Counter

    if len(seg_features) < 2:
        return [(seg_id(seg), 0.0) for seg in cluster]

    # Fit K-Means (same as original)
    from sklearn.cluster import KMeans
    all_descriptors = np.concatenate(list(seg_features.values()))
    kmeans = KMeans(n_clusters=bovw_dict_size, random_state=42)
    kmeans.fit(all_descriptors)

    # Predict visual words per segment
    n_docs = len(seg_features)
    tfs = {}
    for segment, descriptors in seg_features.items():
        labels = kmeans.predict(descriptors)
        tfs[segment] = Counter(labels)

    # Document frequency per visual word
    doc_freq = Counter(key for counts in tfs.values() for key in counts.keys())

    # TF-IDF with CORRECTED IDF = log10(N_docs / doc_freq)
    results = []
    for segment, tf_counts in tfs.items():
        score = 0.0
        for word, tf in tf_counts.items():
            df = doc_freq[word]
            if df >= n_docs:
                idf = 0.0  # appears in all docs → no discrimination
            else:
                idf = log10(n_docs / df)
            score += tf * idf
        results.append((seg_id(segment), score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── SIFT+BoVW scoring (corrected IDF + normalized by frame count) ─────

def run_sift_scoring_normalized(
    cluster: set[VideoSegment],
    seg_features: dict[VideoSegment, np.ndarray],
    bovw_dict_size: int = 300,
) -> list[tuple[str, float]]:
    """
    SIFT+BoVW with CORRECTED IDF, normalized by number of descriptors.
    This makes it measure "average visual richness per descriptor" instead
    of "total visual content volume", comparable to DINOv2's per-frame mean.
    """
    from math import log10
    from collections import Counter

    if len(seg_features) < 2:
        return [(seg_id(seg), 0.0) for seg in cluster]

    from sklearn.cluster import KMeans
    all_descriptors = np.concatenate(list(seg_features.values()))
    kmeans = KMeans(n_clusters=bovw_dict_size, random_state=42)
    kmeans.fit(all_descriptors)

    n_docs = len(seg_features)
    tfs = {}
    n_descriptors = {}
    for segment, descriptors in seg_features.items():
        labels = kmeans.predict(descriptors)
        tfs[segment] = Counter(labels)
        n_descriptors[segment] = len(descriptors)

    doc_freq = Counter(key for counts in tfs.values() for key in counts.keys())

    results = []
    for segment, tf_counts in tfs.items():
        score = 0.0
        for word, tf in tf_counts.items():
            df = doc_freq[word]
            if df >= n_docs:
                idf = 0.0
            else:
                idf = log10(n_docs / df)
            score += tf * idf
        # Normalize by number of descriptors (analogous to DINOv2's mean)
        n_desc = n_descriptors[segment]
        normalized_score = score / n_desc if n_desc > 0 else 0.0
        results.append((seg_id(segment), normalized_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── SIFT+BoVW scoring (corrected IDF + normalized by frame count) ──────

def run_sift_scoring_per_frame(
    cluster: set[VideoSegment],
    seg_features: dict[VideoSegment, np.ndarray],
    bovw_dict_size: int = 300,
) -> list[tuple[str, float]]:
    """
    SIFT+BoVW with CORRECTED IDF, normalized by number of frames.
    Score = (sum TF-IDF with N_docs) / N_frames.
    Removes length bias by converting sum to mean per frame.
    """
    from math import log10
    from collections import Counter

    if len(seg_features) < 2:
        return [(seg_id(seg), 0.0) for seg in cluster]

    from sklearn.cluster import KMeans
    all_descriptors = np.concatenate(list(seg_features.values()))
    kmeans = KMeans(n_clusters=bovw_dict_size, random_state=42)
    kmeans.fit(all_descriptors)

    n_docs = len(seg_features)
    tfs = {}
    for segment, descriptors in seg_features.items():
        labels = kmeans.predict(descriptors)
        tfs[segment] = Counter(labels)

    doc_freq = Counter(key for counts in tfs.values() for key in counts.keys())

    results = []
    for segment, tf_counts in tfs.items():
        score = 0.0
        for word, tf in tf_counts.items():
            df = doc_freq[word]
            if df >= n_docs:
                idf = 0.0
            else:
                idf = log10(n_docs / df)
            score += tf * idf
        # Normalize by frame count (1fps extraction → ~duration frames)
        n_frames = max(1, round(segment.end - segment.start))
        per_frame_score = score / n_frames
        results.append((seg_id(segment), per_frame_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── Per-frame keypoint density (simple baseline) ─────────────────────

def run_keypoint_density_scoring(
    cluster: set[VideoSegment],
) -> list[tuple[str, float]]:
    """
    Simple baseline: average SIFT keypoint count per frame.
    No BoVW, no K-Means — just "how many keypoints per frame on average?"
    """
    from cv2 import SIFT_create

    results = []
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=True,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            results.append((seg_id(segment), 0.0))
            continue

        kp_counts = []
        sift = SIFT_create()
        for frame in frames:
            keypoints, _ = sift.detectAndCompute(frame, None)
            kp_counts.append(len(keypoints) if keypoints else 0)

        avg_kp = float(np.mean(kp_counts)) if kp_counts else 0.0
        results.append((seg_id(segment), avg_kp))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── DINOv2 scoring ────────────────────────────────────────────────────

def run_dinov2_scoring(
    cluster: set[VideoSegment],
    model,
    device: str = "cuda",
    lambda_val: float = 0.0,
) -> list[tuple[str, float, dict]]:
    """
    Run DINOv2 patch-token scoring on a cluster.
    Returns [(seg_id, quality_score, features_dict)] sorted descending.
    """
    segment_features = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            continue
        feats = dinov2_scorer.extract_patch_features(frames, model, device)
        segment_features[seg_id(segment)] = feats

    return dinov2_scorer.score_cluster(segment_features, lambda_val=lambda_val)


# ── ResNet-50 scoring ────────────────────────────────────────────────

def run_resnet50_scoring(
    cluster: set[VideoSegment],
    model,
    device: str = "cuda",
    lambda_val: float = 0.0,
) -> list[tuple[str, float, dict]]:
    """
    Run ResNet-50 GAP feature scoring on a cluster.
    Returns [(seg_id, quality_score, features_dict)] sorted descending.
    """
    segment_features = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            continue
        feats = resnet50_scorer.extract_features(frames, model, device)
        segment_features[seg_id(segment)] = feats

    return resnet50_scorer.score_cluster(segment_features, lambda_val=lambda_val)


# ── QualiCLIP scoring (learned NR-IQA) ───────────────────────────────

def run_qualiclip_scoring(
    cluster: set[VideoSegment],
    model,
    device: str = "cuda",
) -> list[tuple[str, float, dict]]:
    """
    Run QualiCLIP NR-IQA scoring on a cluster.
    Returns [(seg_id, quality_score, features_dict)] sorted descending.
    """
    segment_scores = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            continue
        scores = qualiclip_scorer.score_frames(frames, model, device)
        segment_scores[seg_id(segment)] = scores

    return qualiclip_scorer.score_cluster(segment_scores)


# ── LIQE scoring (learned multi-task NR-IQA) ─────────────────────────

def run_liqe_scoring(cluster, model, device="cuda"):
    segment_scores = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            continue
        scores = liqe_scorer.score_frames(frames, model, device)
        segment_scores[seg_id(segment)] = scores
    return liqe_scorer.score_cluster(segment_scores)


# ── BRISQUE/NIQE scoring (classic NR-IQA) ────────────────────────────

def run_classic_iqa_scoring(cluster, model, device="cuda", lower_better=True):
    segment_scores = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            continue
        scores = classic_iqa_scorer.score_frames(frames, model, device)
        segment_scores[seg_id(segment)] = scores
    return classic_iqa_scorer.score_cluster(segment_scores, lower_better=lower_better)


# ── SI/TI scoring (ITU-T P.910) ─────────────────────────────────────

def run_si_ti_scoring(
    cluster: set[VideoSegment],
) -> tuple[list[tuple[str, float, dict]], dict[str, np.ndarray], dict[str, np.ndarray]]:
    """
    Run SI/TI scoring on a cluster. No model needed (CPU-only, pure OpenCV).

    Returns:
        - ranked results: [(seg_id, mean_si, features_dict)] sorted descending
        - segment_si: {seg_id: (n_frames,) SI per frame} — for correlation analysis
        - segment_ti: {seg_id: (n_frames,) TI per frame}
    """
    segment_si = {}
    segment_ti = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            continue
        sid = seg_id(segment)
        segment_si[sid] = si_ti_scorer.compute_si_per_frame(frames)
        segment_ti[sid] = si_ti_scorer.compute_ti_per_frame(frames)

    ranked = si_ti_scorer.score_cluster(segment_si, segment_ti)
    return ranked, segment_si, segment_ti


# ── Q-Align scoring (LMM-based NR-IQA) ─────────────────────────────

def run_qalign_scoring(
    cluster: set[VideoSegment],
    model,
    device: str = "cuda",
) -> list[tuple[str, float, dict]]:
    """
    Run Q-Align 4-bit NR-IQA scoring on a cluster.
    Returns [(seg_id, quality_score, features_dict)] sorted descending.
    """
    segment_scores = {}
    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )
        if not frames:
            continue
        scores = qalign_scorer.score_frames(frames, model, device)
        segment_scores[seg_id(segment)] = scores

    return qalign_scorer.score_cluster(segment_scores)


# ── Metrics ───────────────────────────────────────────────────────────

def compute_metrics(sift_results: list, dinov2_results: list) -> dict:
    """Compute comparison metrics for a single cluster."""
    if not sift_results or not dinov2_results:
        return {"agreement": None, "kendall_tau": None, "spearman_rho": None}

    sift_top1 = sift_results[0][0]
    dinov2_top1 = dinov2_results[0][0]
    agreement = sift_top1 == dinov2_top1

    # Build ranking vectors for correlation
    sift_ids = [r[0] for r in sift_results]
    dinov2_ids = [r[0] for r in dinov2_results]
    common_ids = [sid for sid in sift_ids if sid in dinov2_ids]

    if len(common_ids) < 2:
        return {"agreement": agreement, "kendall_tau": None, "spearman_rho": None}

    sift_ranks = [sift_ids.index(sid) for sid in common_ids]
    dinov2_ranks = [dinov2_ids.index(sid) for sid in common_ids]

    tau, _ = kendalltau(sift_ranks, dinov2_ranks)
    rho, _ = spearmanr(sift_ranks, dinov2_ranks)

    return {"agreement": agreement, "kendall_tau": tau, "spearman_rho": rho}


# ── Main benchmark ────────────────────────────────────────────────────

def run_benchmark(dataset_json: str, dataset_name: str):
    log.info(f"=== Benchmark: {dataset_name} ===")

    # 1. Load dataset
    log.info("Loading dataset...")
    videos = VideoLoader.load_videos_from_json(dataset_json)
    total_segments = sum(len(v.segments) for v in videos)
    log.info(f"Loaded {len(videos)} videos, {total_segments} segments")

    # 2. Run Stage 3 (ContentBasedRedundancy) to get clusters
    log.info("Running Stage 3 (ContentBasedRedundancy)...")
    handler = SummarySegmentHandler()
    handler.set_source_videos(videos)
    stage3 = ContentBasedRedundancy()
    handler = stage3.evaluate(handler)

    clusters = handler.agent_logs["ContentBasedRedundancy"].pick
    log.info(f"Stage 3 produced {len(clusters)} redundancy clusters")

    if not clusters:
        log.warning("No clusters found. Cannot run Stage 4 comparison.")
        return

    for i, cluster in enumerate(clusters):
        log.info(f"  Cluster {i}: {len(cluster)} segments")
        for seg in cluster:
            log.info(f"    - {seg_id(seg)} ({seg.end - seg.start:.1f}s)")

    # 3. Q-Align pass (dedicated — uses ~5GB VRAM, can't coexist with other models)
    log.info("=== Phase 1: Q-Align (dedicated GPU pass) ===")
    log.info("Loading Q-Align 4-bit (LMM NR-IQA, ~5GB VRAM)...")
    qalign_model = qalign_scorer.load_model(device="cuda")
    log.info(f"Q-Align 4-bit loaded. VRAM: {torch.cuda.memory_allocated()/1e9:.2f}GB")

    qalign_all_results = {}  # cluster_idx -> results
    qalign_all_times = {}
    for ci, cluster in enumerate(clusters):
        log.info(f"  Q-Align scoring cluster {ci} ({len(cluster)} segments)...")
        t0 = time.perf_counter()
        qalign_all_results[ci] = run_qalign_scoring(cluster, qalign_model)
        qalign_all_times[ci] = time.perf_counter() - t0
        for rank, (sid, score, feats) in enumerate(qalign_all_results[ci]):
            log.info(
                f"    rank {rank}: {sid} = {score:.4f} "
                f"(std={feats['std_score']:.4f})"
            )

    qalign_scorer.unload_model(qalign_model)
    log.info("Q-Align unloaded. GPU freed.")

    # 3b. Load all other models (total ~0.7GB VRAM)
    log.info("=== Phase 2: All other models ===")
    log.info("Loading DINOv2 ViT-S/14 (with registers)...")
    dinov2_model = dinov2_scorer.load_model("dinov2_vits14_reg", device="cuda")
    log.info("DINOv2 loaded on GPU (fp16)")

    log.info("Loading ResNet-50 (ImageNet supervised)...")
    resnet50_model = resnet50_scorer.load_model(device="cuda")
    log.info("ResNet-50 loaded on GPU (fp16)")

    log.info("Loading QualiCLIP (learned NR-IQA)...")
    qualiclip_model = qualiclip_scorer.load_model(device="cuda")
    log.info("QualiCLIP loaded on GPU")

    log.info("Loading LIQE (multi-task NR-IQA)...")
    liqe_model = liqe_scorer.load_model(device="cuda")
    log.info("LIQE loaded on GPU")

    log.info("Loading BRISQUE (classic NR-IQA)...")
    brisque_model = classic_iqa_scorer.load_model("brisque", device="cuda")
    log.info("BRISQUE loaded")

    log.info("Loading NIQE (classic NR-IQA)...")
    niqe_model = classic_iqa_scorer.load_model("niqe", device="cuda")
    log.info("NIQE loaded")

    # SI/TI needs no model (CPU-only, pure OpenCV)
    log.info("SI/TI scorer ready (CPU-only, no model loading needed)")
    log.info(f"All models loaded. Total VRAM: {torch.cuda.memory_allocated()/1e9:.2f}GB")

    # 3c. Load CNN models for BoVW (spatial features, one at a time per cluster)
    log.info("CNN BoVW models will be loaded per-cluster to save GPU memory")

    # 4. Run all methods on each cluster (except Q-Align, already done)
    all_rows = []
    all_metrics = []

    for cluster_idx, cluster in enumerate(clusters):
        log.info(f"\n--- Cluster {cluster_idx} ({len(cluster)} segments) ---")

        # Extract SIFT features ONCE (shared by buggy and corrected)
        log.info("Extracting SIFT features...")
        t0 = time.perf_counter()
        seg_features = extract_sift_features(cluster)
        sift_extract_time = time.perf_counter() - t0
        log.info(f"SIFT extraction done in {sift_extract_time:.2f}s ({len(seg_features)} segments)")

        # (A) SIFT+BoVW with BUGGY IDF (original)
        log.info("Running SIFT+BoVW (buggy IDF: dict_size=300)...")
        t0 = time.perf_counter()
        sift_buggy_results = run_sift_scoring_buggy(cluster, seg_features)
        sift_buggy_time = sift_extract_time + (time.perf_counter() - t0)

        for rank, (sid, score) in enumerate(sift_buggy_results):
            log.info(f"  SIFT-buggy rank {rank}: {sid} = {score:.4f}")

        # (B) SIFT+BoVW with CORRECTED IDF (N_docs)
        log.info("Running SIFT+BoVW (corrected IDF: N_docs)...")
        t0 = time.perf_counter()
        sift_fixed_results = run_sift_scoring_corrected(cluster, seg_features)
        sift_fixed_time = sift_extract_time + (time.perf_counter() - t0)

        for rank, (sid, score) in enumerate(sift_fixed_results):
            log.info(f"  SIFT-fixed rank {rank}: {sid} = {score:.4f}")

        # (B2) SIFT+BoVW corrected + normalized by descriptor count
        log.info("Running SIFT+BoVW (corrected + normalized)...")
        t0 = time.perf_counter()
        sift_norm_results = run_sift_scoring_normalized(cluster, seg_features)
        sift_norm_time = sift_extract_time + (time.perf_counter() - t0)

        for rank, (sid, score) in enumerate(sift_norm_results):
            log.info(f"  SIFT-norm  rank {rank}: {sid} = {score:.6f}")

        # (B3) SIFT+BoVW corrected + normalized by frame count
        log.info("Running SIFT+BoVW (corrected + per-frame)...")
        t0 = time.perf_counter()
        sift_frame_results = run_sift_scoring_per_frame(cluster, seg_features)
        sift_frame_time = sift_extract_time + (time.perf_counter() - t0)

        for rank, (sid, score) in enumerate(sift_frame_results):
            log.info(f"  SIFT/frame rank {rank}: {sid} = {score:.4f}")

        # (D) Keypoint density (simple per-frame baseline)
        log.info("Running keypoint density...")
        t0 = time.perf_counter()
        kp_density_results = run_keypoint_density_scoring(cluster)
        kp_density_time = time.perf_counter() - t0

        for rank, (sid, score) in enumerate(kp_density_results):
            log.info(f"  KP-density rank {rank}: {sid} = {score:.1f}")

        # (C) DINOv2
        log.info("Running DINOv2...")
        t0 = time.perf_counter()
        dinov2_results = run_dinov2_scoring(cluster, dinov2_model)
        dinov2_time = time.perf_counter() - t0

        for rank, (sid, score, feats) in enumerate(dinov2_results):
            log.info(
                f"  DINOv2 rank {rank}: {sid} = {score:.4f} "
                f"(R={feats['coherence_R']:.3f}, std={feats['std_norm']:.4f})"
            )

        # (G) ResNet-50
        log.info("Running ResNet-50...")
        t0 = time.perf_counter()
        resnet50_results = run_resnet50_scoring(cluster, resnet50_model)
        resnet50_time = time.perf_counter() - t0

        for rank, (sid, score, feats) in enumerate(resnet50_results):
            log.info(
                f"  ResNet-50 rank {rank}: {sid} = {score:.4f} "
                f"(R={feats['coherence_R']:.3f}, std={feats['std_norm']:.4f})"
            )

        # (H) QualiCLIP (learned NR-IQA — actual quality metric)
        log.info("Running QualiCLIP...")
        t0 = time.perf_counter()
        qualiclip_results = run_qualiclip_scoring(cluster, qualiclip_model)
        qualiclip_time = time.perf_counter() - t0

        for rank, (sid, score, feats) in enumerate(qualiclip_results):
            log.info(
                f"  QualiCLIP rank {rank}: {sid} = {score:.4f} "
                f"(std={feats['std_score']:.4f}, min={feats['min_score']:.4f}, max={feats['max_score']:.4f})"
            )

        # (I) LIQE
        log.info("Running LIQE...")
        t0 = time.perf_counter()
        liqe_results = run_liqe_scoring(cluster, liqe_model)
        liqe_time = time.perf_counter() - t0
        for rank, (sid, score, feats) in enumerate(liqe_results):
            log.info(f"  LIQE rank {rank}: {sid} = {score:.4f} (std={feats['std_score']:.4f})")

        # (J) BRISQUE (lower=better)
        log.info("Running BRISQUE...")
        t0 = time.perf_counter()
        brisque_results = run_classic_iqa_scoring(cluster, brisque_model, lower_better=True)
        brisque_time = time.perf_counter() - t0
        for rank, (sid, score, feats) in enumerate(brisque_results):
            log.info(f"  BRISQUE rank {rank}: {sid} = {score:.2f} (lower=better, iqr={feats['iqr']:.2f})")

        # (K) NIQE (lower=better)
        log.info("Running NIQE...")
        t0 = time.perf_counter()
        niqe_results = run_classic_iqa_scoring(cluster, niqe_model, lower_better=True)
        niqe_time = time.perf_counter() - t0
        for rank, (sid, score, feats) in enumerate(niqe_results):
            log.info(f"  NIQE rank {rank}: {sid} = {score:.4f} (lower=better, iqr={feats['iqr']:.4f})")

        # (L) SI/TI (ITU-T P.910 — CPU-only)
        log.info("Running SI/TI...")
        t0 = time.perf_counter()
        si_ti_results, segment_si, segment_ti = run_si_ti_scoring(cluster)
        si_ti_time = time.perf_counter() - t0
        for rank, (sid, score, feats) in enumerate(si_ti_results):
            log.info(
                f"  SI/TI rank {rank}: {sid} SI_mean={score:.2f} "
                f"(SI_max={feats['si_max']:.2f}, TI_mean={feats['ti_mean']:.2f})"
            )

        # SI vs DINOv2 frame-level correlation (novel analysis)
        # Collect per-frame DINOv2 norms for correlation
        segment_dinov2_norms = {}
        for segment in cluster:
            sid_s = seg_id(segment)
            frames = VideoProcessor.retrieve_video_frames(
                segment.video_path, grayscale=False,
                start_second=segment.start, end_second=segment.end,
            )
            if not frames:
                continue
            feats_d = dinov2_scorer.extract_patch_features(frames, dinov2_model, "cuda")
            per_frame_norms = np.linalg.norm(feats_d, axis=1)
            segment_dinov2_norms[sid_s] = per_frame_norms

        si_dinov2_corr = si_ti_scorer.compute_si_dinov2_correlation(
            segment_si, segment_dinov2_norms
        )
        log.info(
            f"  SI-vs-DINOv2 frame-level correlation: "
            f"Pearson r={si_dinov2_corr['pearson_r']:.4f} (p={si_dinov2_corr['pearson_p']:.2e}), "
            f"Spearman rho={si_dinov2_corr['spearman_rho']:.4f} (p={si_dinov2_corr['spearman_p']:.2e}), "
            f"n_frames={si_dinov2_corr['n_frames']}"
            if si_dinov2_corr['pearson_r'] is not None
            else f"  SI-vs-DINOv2 correlation: insufficient data"
        )

        # (M) Q-Align 4-bit (pre-computed in Phase 1)
        qalign_results = qalign_all_results[cluster_idx]
        qalign_time = qalign_all_times[cluster_idx]
        log.info(f"Q-Align results (pre-computed, {qalign_time:.1f}s):")
        for rank, (sid, score, feats) in enumerate(qalign_results):
            log.info(
                f"  Q-Align rank {rank}: {sid} = {score:.4f} "
                f"(std={feats['std_score']:.4f}, min={feats['min_score']:.4f}, max={feats['max_score']:.4f})"
            )

        # (N-...) CNN BoVW methods — same BoVW+TF-IDF, only SIFT replaced
        cnn_bovw_results = {}
        cnn_bovw_times = {}
        for cnn_name in cnn_bovw_scorer.ALL_CNN_NAMES:
            log.info(f"Running {cnn_name}+BoVW...")
            cnn_model = cnn_bovw_scorer.load_model(cnn_name, device="cuda")
            t0 = time.perf_counter()
            cnn_features = cnn_bovw_scorer.extract_features(cluster, cnn_model, device="cuda")
            cnn_scoring = run_sift_scoring_corrected(cluster, cnn_features)
            cnn_bovw_times[cnn_name] = time.perf_counter() - t0
            cnn_bovw_results[cnn_name] = cnn_scoring
            cnn_bovw_scorer.unload_model(cnn_model)
            for rank, (sid, score) in enumerate(cnn_scoring):
                log.info(f"  {cnn_name}+BoVW rank {rank}: {sid} = {score:.4f}")

        # Metrics: pairwise comparisons (all methods vs DINOv2 + cross)
        m_buggy_vs_dinov2 = compute_metrics(sift_buggy_results, dinov2_results)
        m_fixed_vs_dinov2 = compute_metrics(sift_fixed_results, dinov2_results)
        m_norm_vs_dinov2 = compute_metrics(sift_norm_results, dinov2_results)
        m_frame_vs_dinov2 = compute_metrics(sift_frame_results, dinov2_results)
        m_kpdensity_vs_dinov2 = compute_metrics(kp_density_results, dinov2_results)
        m_buggy_vs_fixed = compute_metrics(sift_buggy_results, sift_fixed_results)
        m_buggy_vs_norm = compute_metrics(sift_buggy_results, sift_norm_results)
        m_frame_vs_kpdensity = compute_metrics(sift_frame_results, kp_density_results)
        m_resnet50_vs_dinov2 = compute_metrics(resnet50_results, dinov2_results)
        m_resnet50_vs_sift_buggy = compute_metrics(resnet50_results, sift_buggy_results)
        m_resnet50_vs_kpdensity = compute_metrics(resnet50_results, kp_density_results)
        m_qualiclip_vs_dinov2 = compute_metrics(qualiclip_results, dinov2_results)
        m_qualiclip_vs_sift_buggy = compute_metrics(qualiclip_results, sift_buggy_results)
        m_qualiclip_vs_resnet50 = compute_metrics(qualiclip_results, resnet50_results)
        m_qualiclip_vs_kpdensity = compute_metrics(qualiclip_results, kp_density_results)
        m_liqe_vs_dinov2 = compute_metrics(liqe_results, dinov2_results)
        m_liqe_vs_qualiclip = compute_metrics(liqe_results, qualiclip_results)
        m_liqe_vs_sift_buggy = compute_metrics(liqe_results, sift_buggy_results)
        m_brisque_vs_dinov2 = compute_metrics(brisque_results, dinov2_results)
        m_brisque_vs_qualiclip = compute_metrics(brisque_results, qualiclip_results)
        m_niqe_vs_dinov2 = compute_metrics(niqe_results, dinov2_results)
        m_niqe_vs_qualiclip = compute_metrics(niqe_results, qualiclip_results)

        # SI/TI pairwise metrics
        m_si_vs_dinov2 = compute_metrics(si_ti_results, dinov2_results)
        m_si_vs_qualiclip = compute_metrics(si_ti_results, qualiclip_results)
        m_si_vs_sift_buggy = compute_metrics(si_ti_results, sift_buggy_results)
        m_si_vs_qalign = compute_metrics(si_ti_results, qalign_results)

        # Q-Align pairwise metrics
        m_qalign_vs_dinov2 = compute_metrics(qalign_results, dinov2_results)
        m_qalign_vs_qualiclip = compute_metrics(qalign_results, qualiclip_results)
        m_qalign_vs_sift_buggy = compute_metrics(qalign_results, sift_buggy_results)
        m_qalign_vs_brisque = compute_metrics(qalign_results, brisque_results)
        m_qalign_vs_niqe = compute_metrics(qalign_results, niqe_results)
        m_qalign_vs_liqe = compute_metrics(qalign_results, liqe_results)

        # CNN BoVW pairwise metrics
        cnn_bovw_metrics = {}
        for cnn_name, cnn_res in cnn_bovw_results.items():
            cnn_bovw_metrics[f"{cnn_name}_bovw_vs_sift_buggy"] = compute_metrics(cnn_res, sift_buggy_results)
            cnn_bovw_metrics[f"{cnn_name}_bovw_vs_sift_fixed"] = compute_metrics(cnn_res, sift_fixed_results)
            cnn_bovw_metrics[f"{cnn_name}_bovw_vs_dinov2"] = compute_metrics(cnn_res, dinov2_results)
            cnn_bovw_metrics[f"{cnn_name}_bovw_vs_qualiclip"] = compute_metrics(cnn_res, qualiclip_results)

        metrics = {
            "cluster_idx": cluster_idx,
            "cluster_size": len(cluster),
            "sift_buggy_time_s": sift_buggy_time,
            "sift_fixed_time_s": sift_fixed_time,
            "sift_norm_time_s": sift_norm_time,
            "sift_frame_time_s": sift_frame_time,
            "kp_density_time_s": kp_density_time,
            "dinov2_time_s": dinov2_time,
            "resnet50_time_s": resnet50_time,
            "buggy_vs_dinov2": m_buggy_vs_dinov2,
            "fixed_vs_dinov2": m_fixed_vs_dinov2,
            "norm_vs_dinov2": m_norm_vs_dinov2,
            "frame_vs_dinov2": m_frame_vs_dinov2,
            "kpdensity_vs_dinov2": m_kpdensity_vs_dinov2,
            "buggy_vs_fixed": m_buggy_vs_fixed,
            "buggy_vs_norm": m_buggy_vs_norm,
            "frame_vs_kpdensity": m_frame_vs_kpdensity,
            "resnet50_vs_dinov2": m_resnet50_vs_dinov2,
            "resnet50_vs_sift_buggy": m_resnet50_vs_sift_buggy,
            "resnet50_vs_kpdensity": m_resnet50_vs_kpdensity,
            "qualiclip_vs_dinov2": m_qualiclip_vs_dinov2,
            "qualiclip_vs_sift_buggy": m_qualiclip_vs_sift_buggy,
            "qualiclip_vs_resnet50": m_qualiclip_vs_resnet50,
            "qualiclip_vs_kpdensity": m_qualiclip_vs_kpdensity,
            "qualiclip_time_s": qualiclip_time,
            "liqe_vs_dinov2": m_liqe_vs_dinov2,
            "liqe_vs_qualiclip": m_liqe_vs_qualiclip,
            "liqe_vs_sift_buggy": m_liqe_vs_sift_buggy,
            "liqe_time_s": liqe_time,
            "brisque_vs_dinov2": m_brisque_vs_dinov2,
            "brisque_vs_qualiclip": m_brisque_vs_qualiclip,
            "brisque_time_s": brisque_time,
            "niqe_vs_dinov2": m_niqe_vs_dinov2,
            "niqe_vs_qualiclip": m_niqe_vs_qualiclip,
            "niqe_time_s": niqe_time,
            "si_vs_dinov2": m_si_vs_dinov2,
            "si_vs_qualiclip": m_si_vs_qualiclip,
            "si_vs_sift_buggy": m_si_vs_sift_buggy,
            "si_vs_qalign": m_si_vs_qalign,
            "si_ti_time_s": si_ti_time,
            "si_dinov2_frame_correlation": si_dinov2_corr,
            "qalign_vs_dinov2": m_qalign_vs_dinov2,
            "qalign_vs_qualiclip": m_qalign_vs_qualiclip,
            "qalign_vs_sift_buggy": m_qalign_vs_sift_buggy,
            "qalign_vs_brisque": m_qalign_vs_brisque,
            "qalign_vs_niqe": m_qalign_vs_niqe,
            "qalign_vs_liqe": m_qalign_vs_liqe,
            "qalign_time_s": qalign_time,
        }
        # CNN BoVW times and metrics
        for cnn_name in cnn_bovw_scorer.ALL_CNN_NAMES:
            metrics[f"{cnn_name}_bovw_time_s"] = cnn_bovw_times.get(cnn_name, 0)
        metrics.update(cnn_bovw_metrics)
        all_metrics.append(metrics)

        # Log comparisons
        for label, m in [("buggy-vs-dinov2", m_buggy_vs_dinov2),
                         ("fixed-vs-dinov2", m_fixed_vs_dinov2),
                         ("norm-vs-dinov2", m_norm_vs_dinov2),
                         ("frame-vs-dinov2", m_frame_vs_dinov2),
                         ("kpdensity-vs-dinov2", m_kpdensity_vs_dinov2),
                         ("resnet50-vs-dinov2", m_resnet50_vs_dinov2),
                         ("resnet50-vs-sift-buggy", m_resnet50_vs_sift_buggy),
                         ("resnet50-vs-kpdensity", m_resnet50_vs_kpdensity),
                         ("qualiclip-vs-dinov2", m_qualiclip_vs_dinov2),
                         ("qualiclip-vs-sift-buggy", m_qualiclip_vs_sift_buggy),
                         ("qualiclip-vs-resnet50", m_qualiclip_vs_resnet50),
                         ("qualiclip-vs-kpdensity", m_qualiclip_vs_kpdensity),
                         ("liqe-vs-dinov2", m_liqe_vs_dinov2),
                         ("liqe-vs-qualiclip", m_liqe_vs_qualiclip),
                         ("liqe-vs-sift-buggy", m_liqe_vs_sift_buggy),
                         ("brisque-vs-dinov2", m_brisque_vs_dinov2),
                         ("brisque-vs-qualiclip", m_brisque_vs_qualiclip),
                         ("niqe-vs-dinov2", m_niqe_vs_dinov2),
                         ("niqe-vs-qualiclip", m_niqe_vs_qualiclip),
                         ("si-vs-dinov2", m_si_vs_dinov2),
                         ("si-vs-qualiclip", m_si_vs_qualiclip),
                         ("si-vs-sift-buggy", m_si_vs_sift_buggy),
                         ("si-vs-qalign", m_si_vs_qalign),
                         ("qalign-vs-dinov2", m_qalign_vs_dinov2),
                         ("qalign-vs-qualiclip", m_qalign_vs_qualiclip),
                         ("qalign-vs-sift-buggy", m_qalign_vs_sift_buggy),
                         ("qalign-vs-brisque", m_qalign_vs_brisque),
                         ("qalign-vs-niqe", m_qalign_vs_niqe),
                         ("qalign-vs-liqe", m_qalign_vs_liqe),
                         ("buggy-vs-fixed", m_buggy_vs_fixed),
                         ("buggy-vs-norm", m_buggy_vs_norm),
                         ("frame-vs-kpdensity", m_frame_vs_kpdensity)]:
            agree = "AGREE" if m["agreement"] else "DISAGREE"
            tau_str = f"tau={m['kendall_tau']:.3f}" if m["kendall_tau"] is not None else "tau=N/A"
            log.info(f"  {label}: {agree} | {tau_str}")
        for key, m in cnn_bovw_metrics.items():
            agree = "AGREE" if m["agreement"] else "DISAGREE"
            tau_str = f"tau={m['kendall_tau']:.3f}" if m["kendall_tau"] is not None else "tau=N/A"
            log.info(f"  {key}: {agree} | {tau_str}")

        # Build rows for CSV
        sift_buggy_dict = {sid: (rank, score) for rank, (sid, score) in enumerate(sift_buggy_results)}
        sift_fixed_dict = {sid: (rank, score) for rank, (sid, score) in enumerate(sift_fixed_results)}
        sift_norm_dict = {sid: (rank, score) for rank, (sid, score) in enumerate(sift_norm_results)}
        sift_frame_dict = {sid: (rank, score) for rank, (sid, score) in enumerate(sift_frame_results)}
        kp_density_dict = {sid: (rank, score) for rank, (sid, score) in enumerate(kp_density_results)}
        dinov2_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(dinov2_results)}
        resnet50_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(resnet50_results)}
        qualiclip_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(qualiclip_results)}
        liqe_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(liqe_results)}
        brisque_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(brisque_results)}
        niqe_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(niqe_results)}
        si_ti_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(si_ti_results)}
        qalign_dict = {sid: (rank, score, feats) for rank, (sid, score, feats) in enumerate(qalign_results)}

        # CNN BoVW dicts for CSV
        cnn_bovw_dicts = {}
        for cnn_name, cnn_res in cnn_bovw_results.items():
            cnn_bovw_dicts[cnn_name] = {sid: (rank, score) for rank, (sid, score) in enumerate(cnn_res)}

        all_segment_ids = (
            set(s[0] for s in sift_buggy_results)
            | set(s[0] for s in dinov2_results)
            | set(s[0] for s in resnet50_results)
            | set(s[0] for s in qualiclip_results)
        )
        for sid in sorted(all_segment_ids):
            row = {
                "dataset": dataset_name,
                "cluster_idx": cluster_idx,
                "segment_id": sid,
            }
            if sid in sift_buggy_dict:
                row["sift_buggy_rank"] = sift_buggy_dict[sid][0]
                row["sift_buggy_score"] = sift_buggy_dict[sid][1]
            if sid in sift_fixed_dict:
                row["sift_fixed_rank"] = sift_fixed_dict[sid][0]
                row["sift_fixed_score"] = sift_fixed_dict[sid][1]
            if sid in sift_norm_dict:
                row["sift_norm_rank"] = sift_norm_dict[sid][0]
                row["sift_norm_score"] = sift_norm_dict[sid][1]
            if sid in sift_frame_dict:
                row["sift_frame_rank"] = sift_frame_dict[sid][0]
                row["sift_frame_score"] = sift_frame_dict[sid][1]
            if sid in kp_density_dict:
                row["kp_density_rank"] = kp_density_dict[sid][0]
                row["kp_density_score"] = kp_density_dict[sid][1]
            if sid in dinov2_dict:
                row["dinov2_rank"] = dinov2_dict[sid][0]
                row["dinov2_score"] = dinov2_dict[sid][1]
                row["dinov2_mean_norm"] = dinov2_dict[sid][2]["mean_norm"]
                row["dinov2_centroid_norm"] = dinov2_dict[sid][2]["centroid_norm"]
                row["dinov2_coherence_R"] = dinov2_dict[sid][2]["coherence_R"]
                row["dinov2_std_norm"] = dinov2_dict[sid][2]["std_norm"]
            if sid in resnet50_dict:
                row["resnet50_rank"] = resnet50_dict[sid][0]
                row["resnet50_score"] = resnet50_dict[sid][1]
                row["resnet50_mean_norm"] = resnet50_dict[sid][2]["mean_norm"]
                row["resnet50_centroid_norm"] = resnet50_dict[sid][2]["centroid_norm"]
                row["resnet50_coherence_R"] = resnet50_dict[sid][2]["coherence_R"]
                row["resnet50_std_norm"] = resnet50_dict[sid][2]["std_norm"]
            if sid in qualiclip_dict:
                row["qualiclip_rank"] = qualiclip_dict[sid][0]
                row["qualiclip_score"] = qualiclip_dict[sid][1]
                row["qualiclip_mean"] = qualiclip_dict[sid][2]["mean_score"]
                row["qualiclip_std"] = qualiclip_dict[sid][2]["std_score"]
                row["qualiclip_min"] = qualiclip_dict[sid][2]["min_score"]
                row["qualiclip_max"] = qualiclip_dict[sid][2]["max_score"]
            if sid in liqe_dict:
                row["liqe_rank"] = liqe_dict[sid][0]
                row["liqe_score"] = liqe_dict[sid][1]
                row["liqe_std"] = liqe_dict[sid][2]["std_score"]
            if sid in brisque_dict:
                row["brisque_rank"] = brisque_dict[sid][0]
                row["brisque_score"] = brisque_dict[sid][1]
                row["brisque_std"] = brisque_dict[sid][2]["std_score"]
                row["brisque_iqr"] = brisque_dict[sid][2]["iqr"]
            if sid in niqe_dict:
                row["niqe_rank"] = niqe_dict[sid][0]
                row["niqe_score"] = niqe_dict[sid][1]
                row["niqe_std"] = niqe_dict[sid][2]["std_score"]
                row["niqe_iqr"] = niqe_dict[sid][2]["iqr"]
            if sid in si_ti_dict:
                row["si_rank"] = si_ti_dict[sid][0]
                row["si_score"] = si_ti_dict[sid][1]
                row["si_mean"] = si_ti_dict[sid][2]["si_mean"]
                row["si_std"] = si_ti_dict[sid][2]["si_std"]
                row["si_max"] = si_ti_dict[sid][2]["si_max"]
                row["ti_mean"] = si_ti_dict[sid][2]["ti_mean"]
                row["ti_std"] = si_ti_dict[sid][2]["ti_std"]
                row["ti_max"] = si_ti_dict[sid][2]["ti_max"]
            if sid in qalign_dict:
                row["qalign_rank"] = qalign_dict[sid][0]
                row["qalign_score"] = qalign_dict[sid][1]
                row["qalign_mean"] = qalign_dict[sid][2]["mean_score"]
                row["qalign_std"] = qalign_dict[sid][2]["std_score"]
                row["qalign_min"] = qalign_dict[sid][2]["min_score"]
                row["qalign_max"] = qalign_dict[sid][2]["max_score"]
                row["qalign_median"] = qalign_dict[sid][2]["median_score"]
            for cnn_name, cnn_dict in cnn_bovw_dicts.items():
                if sid in cnn_dict:
                    row[f"{cnn_name}_bovw_rank"] = cnn_dict[sid][0]
                    row[f"{cnn_name}_bovw_score"] = cnn_dict[sid][1]
            all_rows.append(row)

    # 5. Unload models
    dinov2_scorer.unload_model(dinov2_model)
    resnet50_scorer.unload_model(resnet50_model)
    qualiclip_scorer.unload_model(qualiclip_model)
    liqe_scorer.unload_model(liqe_model)
    classic_iqa_scorer.unload_model(brisque_model)
    classic_iqa_scorer.unload_model(niqe_model)
    # Q-Align already unloaded after Phase 1
    log.info("All models unloaded from GPU")

    # 6. Save results
    RESULTS_DIR.mkdir(exist_ok=True)

    # CSV with per-segment scores (new file to preserve original)
    df = pd.DataFrame(all_rows)
    csv_path = RESULTS_DIR / f"{dataset_name}_full_comparison.csv"
    df.to_csv(csv_path, index=False)
    log.info(f"Saved comparison CSV: {csv_path}")

    # Metrics JSON
    metrics_summary = {
        "dataset": dataset_name,
        "n_clusters": len(clusters),
        "n_segments_total": total_segments,
        "clusters": all_metrics,
    }

    # Aggregate metrics per comparison pair
    def aggregate_pair(key):
        pairs = [m[key] for m in all_metrics]
        agreements = [p["agreement"] for p in pairs if p["agreement"] is not None]
        taus = [p["kendall_tau"] for p in pairs if p["kendall_tau"] is not None]
        rhos = [p["spearman_rho"] for p in pairs if p["spearman_rho"] is not None]
        return {
            "agreement_rate": sum(agreements) / len(agreements) if agreements else None,
            "mean_kendall_tau": float(np.mean(taus)) if taus else None,
            "mean_spearman_rho": float(np.mean(rhos)) if rhos else None,
        }

    sift_buggy_times = [m["sift_buggy_time_s"] for m in all_metrics]
    dinov2_times = [m["dinov2_time_s"] for m in all_metrics]

    pairs = [
        ("buggy_vs_dinov2", "SIFT-buggy vs DINOv2"),
        ("fixed_vs_dinov2", "SIFT-fixed vs DINOv2"),
        ("norm_vs_dinov2", "SIFT-norm vs DINOv2"),
        ("frame_vs_dinov2", "SIFT/frame vs DINOv2"),
        ("kpdensity_vs_dinov2", "KP-density vs DINOv2"),
        ("resnet50_vs_dinov2", "ResNet-50 vs DINOv2"),
        ("resnet50_vs_sift_buggy", "ResNet-50 vs SIFT-buggy"),
        ("resnet50_vs_kpdensity", "ResNet-50 vs KP-density"),
        ("qualiclip_vs_dinov2", "QualiCLIP vs DINOv2"),
        ("qualiclip_vs_sift_buggy", "QualiCLIP vs SIFT-buggy"),
        ("qualiclip_vs_resnet50", "QualiCLIP vs ResNet-50"),
        ("qualiclip_vs_kpdensity", "QualiCLIP vs KP-density"),
        ("liqe_vs_dinov2", "LIQE vs DINOv2"),
        ("liqe_vs_qualiclip", "LIQE vs QualiCLIP"),
        ("liqe_vs_sift_buggy", "LIQE vs SIFT-buggy"),
        ("brisque_vs_dinov2", "BRISQUE vs DINOv2"),
        ("brisque_vs_qualiclip", "BRISQUE vs QualiCLIP"),
        ("niqe_vs_dinov2", "NIQE vs DINOv2"),
        ("niqe_vs_qualiclip", "NIQE vs QualiCLIP"),
        ("si_vs_dinov2", "SI vs DINOv2"),
        ("si_vs_qualiclip", "SI vs QualiCLIP"),
        ("si_vs_sift_buggy", "SI vs SIFT-buggy"),
        ("si_vs_qalign", "SI vs Q-Align"),
        ("qalign_vs_dinov2", "Q-Align vs DINOv2"),
        ("qalign_vs_qualiclip", "Q-Align vs QualiCLIP"),
        ("qalign_vs_sift_buggy", "Q-Align vs SIFT-buggy"),
        ("qalign_vs_brisque", "Q-Align vs BRISQUE"),
        ("qalign_vs_niqe", "Q-Align vs NIQE"),
        ("qalign_vs_liqe", "Q-Align vs LIQE"),
        ("buggy_vs_fixed", "SIFT-buggy vs SIFT-fixed"),
        ("buggy_vs_norm", "SIFT-buggy vs SIFT-norm"),
        ("frame_vs_kpdensity", "SIFT/frame vs KP-density"),
    ]
    # CNN BoVW pairs
    for cnn_name in cnn_bovw_scorer.ALL_CNN_NAMES:
        pairs.append((f"{cnn_name}_bovw_vs_sift_buggy", f"{cnn_name}+BoVW vs SIFT-buggy"))
        pairs.append((f"{cnn_name}_bovw_vs_sift_fixed", f"{cnn_name}+BoVW vs SIFT-fixed"))
        pairs.append((f"{cnn_name}_bovw_vs_dinov2", f"{cnn_name}+BoVW vs DINOv2"))
        pairs.append((f"{cnn_name}_bovw_vs_qualiclip", f"{cnn_name}+BoVW vs QualiCLIP"))

    metrics_summary["aggregate"] = {}
    for key, _ in pairs:
        metrics_summary["aggregate"][key] = aggregate_pair(key)

    resnet50_times = [m["resnet50_time_s"] for m in all_metrics]
    qualiclip_times = [m["qualiclip_time_s"] for m in all_metrics]

    metrics_summary["aggregate"]["total_sift_time_s"] = sum(sift_buggy_times)
    metrics_summary["aggregate"]["total_dinov2_time_s"] = sum(dinov2_times)
    metrics_summary["aggregate"]["total_resnet50_time_s"] = sum(resnet50_times)
    metrics_summary["aggregate"]["total_qualiclip_time_s"] = sum(qualiclip_times)
    liqe_times = [m["liqe_time_s"] for m in all_metrics]
    brisque_times = [m["brisque_time_s"] for m in all_metrics]
    niqe_times = [m["niqe_time_s"] for m in all_metrics]
    si_ti_times = [m["si_ti_time_s"] for m in all_metrics]
    qalign_times = [m["qalign_time_s"] for m in all_metrics]
    metrics_summary["aggregate"]["total_liqe_time_s"] = sum(liqe_times)
    metrics_summary["aggregate"]["total_brisque_time_s"] = sum(brisque_times)
    metrics_summary["aggregate"]["total_niqe_time_s"] = sum(niqe_times)
    metrics_summary["aggregate"]["total_si_ti_time_s"] = sum(si_ti_times)
    metrics_summary["aggregate"]["total_qalign_time_s"] = sum(qalign_times)

    # Aggregate SI-vs-DINOv2 frame-level correlations
    all_si_corrs = [m["si_dinov2_frame_correlation"] for m in all_metrics]
    valid_corrs = [c for c in all_si_corrs if c.get("pearson_r") is not None]
    if valid_corrs:
        metrics_summary["aggregate"]["si_dinov2_frame_correlation"] = {
            "mean_pearson_r": float(np.mean([c["pearson_r"] for c in valid_corrs])),
            "mean_spearman_rho": float(np.mean([c["spearman_rho"] for c in valid_corrs])),
            "total_frames": sum(c["n_frames"] for c in valid_corrs),
            "per_cluster": all_si_corrs,
        }
    metrics_summary["aggregate"]["speedup_dinov2_vs_sift"] = (
        sum(sift_buggy_times) / sum(dinov2_times) if sum(dinov2_times) > 0 else None
    )
    metrics_summary["aggregate"]["speedup_resnet50_vs_sift"] = (
        sum(sift_buggy_times) / sum(resnet50_times) if sum(resnet50_times) > 0 else None
    )
    for cnn_name in cnn_bovw_scorer.ALL_CNN_NAMES:
        t_key = f"{cnn_name}_bovw_time_s"
        cnn_times = [m.get(t_key, 0) for m in all_metrics]
        metrics_summary["aggregate"][f"total_{t_key}"] = sum(cnn_times)

    metrics_path = RESULTS_DIR / f"{dataset_name}_full_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics_summary, f, indent=2, default=str)
    log.info(f"Saved metrics JSON: {metrics_path}")

    # 7. Print summary
    agg = metrics_summary["aggregate"]
    print("\n" + "=" * 74)
    n_methods = 13 + len(cnn_bovw_scorer.ALL_CNN_NAMES)  # 11 original + SI/TI + Q-Align
    print(f"BENCHMARK RESULTS: {dataset_name} (full comparison — {n_methods} methods)")
    print("=" * 80)
    print(f"Clusters analyzed: {len(clusters)}")
    print()
    print("Methods (proxy):")
    print("  A) SIFT-buggy:  SIFT+BoVW, IDF=log10(300/df)     [original pipeline]")
    print("  B) SIFT-fixed:  SIFT+BoVW, IDF=log10(N_docs/df)  [corrected IDF]")
    print("  C) SIFT-norm:   SIFT+BoVW, corrected + /n_desc   [normalized per descriptor]")
    print("  D) SIFT/frame:  SIFT+BoVW, corrected + /n_frames [normalized per frame]")
    print("  E) KP-density:  mean SIFT keypoints per frame    [simple baseline]")
    print("  F) DINOv2:      mean patch token L2 norm          [ViT self-supervised]")
    print("  G) ResNet-50:   mean GAP feature L2 norm          [CNN supervised]")
    print("Methods (learned NR-IQA):")
    print("  H) QualiCLIP:   CLIP fine-tuned for IQA [0,1]    [Agnolucci 2024]")
    print("  I) LIQE:        multi-task CLIP (qual+dist+scene) [Zhang CVPR 2023]")
    print("Methods (classic NR-IQA — expected ceiling effect):")
    print("  J) BRISQUE:     NSS + SVR (lower=better)          [Mittal 2012]")
    print("  K) NIQE:        NSS opinion-free (lower=better)   [Mittal 2013]")
    print("Methods (complexity metrics — ITU-T P.910):")
    print("  L) SI:          Spatial Information (Sobel std)    [ITU-T P.910]")
    print("     TI:          Temporal Information (frame diff)  [ITU-T P.910]")
    print("Methods (LMM-based NR-IQA — pseudo ground truth):")
    print("  M) Q-Align:     mPLUG-Owl2 7B, 4-bit NF4         [Wu ICML 2024]")
    print("Methods (CNN+BoVW — SIFT replaced, same TF-IDF pipeline):")
    for i, cnn_name in enumerate(cnn_bovw_scorer.ALL_CNN_NAMES):
        letter = chr(ord("L") + i)
        print(f"  {letter}) {cnn_name}+BoVW: CNN spatial features + BoVW+TF-IDF")
    print()

    for key, label in pairs:
        a = agg.get(key)
        if a is None:
            continue
        agree = f"{a['agreement_rate']:.1%}" if a["agreement_rate"] is not None else "N/A"
        tau = f"{a['mean_kendall_tau']:.3f}" if a["mean_kendall_tau"] is not None else "N/A"
        rho = f"{a['mean_spearman_rho']:.3f}" if a["mean_spearman_rho"] is not None else "N/A"
        print(f"  {label:40s}  agree={agree:>6s}  tau={tau:>7s}  rho={rho:>7s}")

    print()
    print(f"  SIFT total time:     {agg['total_sift_time_s']:.2f}s")
    print(f"  DINOv2 total time:   {agg['total_dinov2_time_s']:.2f}s")
    print(f"  ResNet-50 total time:{agg['total_resnet50_time_s']:.2f}s")
    print(f"  QualiCLIP total time:{agg['total_qualiclip_time_s']:.2f}s")
    print(f"  LIQE total time:     {agg['total_liqe_time_s']:.2f}s")
    print(f"  BRISQUE total time:  {agg['total_brisque_time_s']:.2f}s")
    print(f"  NIQE total time:     {agg['total_niqe_time_s']:.2f}s")
    print(f"  SI/TI total time:    {agg['total_si_ti_time_s']:.2f}s")
    print(f"  Q-Align total time:  {agg['total_qalign_time_s']:.2f}s")
    if agg.get("si_dinov2_frame_correlation"):
        corr = agg["si_dinov2_frame_correlation"]
        print(f"\n  SI-vs-DINOv2 frame-level correlation (novel analysis):")
        print(f"    Mean Pearson r:   {corr['mean_pearson_r']:.4f}")
        print(f"    Mean Spearman rho:{corr['mean_spearman_rho']:.4f}")
        print(f"    Total frames:     {corr['total_frames']}")
    if agg["speedup_dinov2_vs_sift"]:
        print(f"  Speedup DINOv2:      {agg['speedup_dinov2_vs_sift']:.1f}x vs SIFT")
    if agg["speedup_resnet50_vs_sift"]:
        print(f"  Speedup ResNet-50:   {agg['speedup_resnet50_vs_sift']:.1f}x vs SIFT")
    for cnn_name in cnn_bovw_scorer.ALL_CNN_NAMES:
        t_key = f"total_{cnn_name}_bovw_time_s"
        if t_key in agg:
            print(f"  {cnn_name}+BoVW time: {agg[t_key]:.2f}s")
    print("=" * 74)

    print("\nPer-segment scores:")
    print(df.to_string(index=False))


if __name__ == "__main__":
    dataset_json = str(PROJECT_DIR / "data" / "bebe_real.json")
    run_benchmark(dataset_json, "bebe_real")
