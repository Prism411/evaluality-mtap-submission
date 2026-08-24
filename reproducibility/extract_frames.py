#!/usr/bin/env python3
"""
Extract representative frames from each segment in redundancy clusters
for manual visual quality evaluation.

Saves frames as JPEG in evaluation/<cluster_N>/<segment_id>/
along with a summary sheet per cluster for side-by-side comparison.
"""

import sys
import json
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, "/dados/MESTRADO-USP/open-video-summary")

from open_video_summary.handlers.summary import SummarySegmentHandler
from open_video_summary.core.selection_criteria.redundancy import ContentBasedRedundancy
from open_video_summary.utils.processing.video import VideoProcessor
from open_video_summary.parsers.video import VideoLoader

PROJECT_DIR = Path(__file__).parent
EVAL_DIR = PROJECT_DIR / "evaluation"


def seg_id(seg):
    video_name = Path(seg.video_path).stem
    return f"{video_name}_{seg.start:.0f}s-{seg.end:.0f}s"


def extract_cluster_frames(cluster, cluster_idx):
    """Extract frames from each segment and save for visual comparison."""
    cluster_dir = EVAL_DIR / f"cluster_{cluster_idx}"
    cluster_dir.mkdir(parents=True, exist_ok=True)

    segment_summaries = []

    for segment in sorted(cluster, key=lambda s: (Path(s.video_path).stem, s.start)):
        sid = seg_id(segment)
        seg_dir = cluster_dir / sid
        seg_dir.mkdir(exist_ok=True)

        # Extract ALL frames at 1 FPS (same as benchmark)
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path, grayscale=False,
            start_second=segment.start, end_second=segment.end,
        )

        if not frames:
            print(f"  WARNING: No frames for {sid}")
            continue

        # Save all frames
        for i, frame in enumerate(frames):
            cv2.imwrite(str(seg_dir / f"frame_{i:03d}.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        # Save first, middle, last as "representative" set
        indices = [0, len(frames) // 2, len(frames) - 1]
        representative = []
        for idx in indices:
            if idx < len(frames):
                representative.append(frames[idx])

        # Create contact sheet (3 frames side by side)
        if representative:
            h = min(f.shape[0] for f in representative)
            resized = []
            for f in representative:
                scale = h / f.shape[0]
                w = int(f.shape[1] * scale)
                resized.append(cv2.resize(f, (w, h)))
            contact = np.hstack(resized)
            cv2.imwrite(str(seg_dir / "contact_sheet.jpg"), contact, [cv2.IMWRITE_JPEG_QUALITY, 90])

        duration = segment.end - segment.start
        n_frames = len(frames)

        # SIFT keypoint count per frame
        sift = cv2.SIFT_create()
        kp_counts = []
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            keypoints, _ = sift.detectAndCompute(gray, None)
            kp_counts.append(len(keypoints) if keypoints else 0)

        segment_summaries.append({
            "segment_id": sid,
            "video": Path(segment.video_path).stem,
            "start": segment.start,
            "end": segment.end,
            "duration_s": round(duration, 1),
            "n_frames": n_frames,
            "avg_keypoints": round(np.mean(kp_counts), 1),
            "min_keypoints": min(kp_counts),
            "max_keypoints": max(kp_counts),
            "content_preview": segment.content[:100] + "..." if len(segment.content) > 100 else segment.content,
        })

        print(f"  {sid}: {n_frames} frames, avg_kp={np.mean(kp_counts):.0f}, saved to {seg_dir}")

    # Save cluster summary JSON
    summary = {
        "cluster_idx": cluster_idx,
        "n_segments": len(segment_summaries),
        "segments": segment_summaries,
        "evaluation_instructions": (
            "Compare the contact_sheet.jpg of each segment side by side. "
            "Which segment has the best visual quality? Consider: "
            "sharpness, noise, compression artifacts, framing, face visibility. "
            "Write your ranking in evaluation_notes.md"
        ),
    }
    with open(cluster_dir / "cluster_info.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Create evaluation template
    eval_template = f"""# Avaliacao Manual — Cluster {cluster_idx}

## Segmentos neste cluster

"""
    for s in segment_summaries:
        eval_template += f"### {s['segment_id']}\n"
        eval_template += f"- Duracao: {s['duration_s']}s ({s['n_frames']} frames)\n"
        eval_template += f"- Keypoints medio: {s['avg_keypoints']}\n"
        eval_template += f"- Conteudo: {s['content_preview']}\n"
        eval_template += f"- Ver: `{s['segment_id']}/contact_sheet.jpg`\n\n"

    eval_template += """## Sua avaliacao

Ranking de qualidade visual (1 = melhor):

| Rank | Segmento | Justificativa |
|------|----------|--------------|
| 1    |          |              |
| 2    |          |              |
| 3    |          |              |

### Observacoes
-
"""
    with open(cluster_dir / "evaluation_notes.md", "w") as f:
        f.write(eval_template)

    return segment_summaries


def main():
    dataset_json = str(PROJECT_DIR / "data" / "bebe_real.json")
    print("Loading dataset...")
    videos = VideoLoader.load_videos_from_json(dataset_json)

    print("Running Stage 3 (redundancy clustering)...")
    handler = SummarySegmentHandler()
    handler.set_source_videos(videos)
    stage3 = ContentBasedRedundancy()
    handler = stage3.evaluate(handler)
    clusters = handler.agent_logs["ContentBasedRedundancy"].pick

    print(f"Found {len(clusters)} clusters\n")

    all_summaries = {}
    for i, cluster in enumerate(clusters):
        print(f"=== Cluster {i} ({len(cluster)} segments) ===")
        summaries = extract_cluster_frames(cluster, i)
        all_summaries[f"cluster_{i}"] = summaries

    # Create top-level evaluation guide
    guide = """# Guia de Avaliacao Visual — Quality Benchmark

## Objetivo
Comparar manualmente qual segmento tem melhor qualidade visual em cada cluster.
Os metodos automaticos (SIFT, DINOv2) discordam — precisamos de ground truth humano.

## Como avaliar

1. Abra cada pasta `cluster_N/`
2. Compare os `contact_sheet.jpg` de cada segmento (first, middle, last frame)
3. Para analise detalhada, veja os frames individuais em `frame_NNN.jpg`
4. Preencha o `evaluation_notes.md` de cada cluster

## Criterios de qualidade
- **Nitidez**: imagem sharp vs borrada
- **Ruido**: limpa vs ruidosa/granulada
- **Artefatos**: compressao, blocking, banding
- **Enquadramento**: composicao, face visibility
- **Iluminacao**: bem iluminada vs escura/superexposta

## Resultados dos metodos automaticos

### Cluster 0 (3 segmentos)
- **SIFT+BoVW escolheu**: jornal_da_record (mais keypoints totais)
- **DINOv2 escolheu**: jornal_da_band (maior norma media de patch tokens)
- **KP-density escolheu**: jornal_da_band (mais keypoints por frame)

### Cluster 1 (2 segmentos)
- **SIFT+BoVW escolheu**: jornal_da_band (mais keypoints totais)
- **DINOv2 escolheu**: jornal_da_record (maior norma media de patch tokens)
- **KP-density escolheu**: jornal_da_record (mais keypoints por frame)

## Pasta `notes/`
Use para anotacoes livres, screenshots, comparacoes extras.
"""
    with open(EVAL_DIR / "README.md", "w") as f:
        f.write(guide)

    # Save global summary
    with open(EVAL_DIR / "extraction_summary.json", "w") as f:
        json.dump(all_summaries, f, indent=2, ensure_ascii=False)

    print(f"\nFrames extracted to: {EVAL_DIR}")
    print("Open each cluster's evaluation_notes.md to record your assessment.")


if __name__ == "__main__":
    main()
