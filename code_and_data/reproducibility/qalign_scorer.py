"""
Q-Align (OneAlign) — LMM-based No-Reference Image Quality Assessment.

Q-Align (Wu et al., ICML 2024) maps MOS to five text quality levels
(excellent/good/fair/poor/bad) and extracts softmax-weighted log probabilities
to produce continuous quality scores. Built on mPLUG-Owl2 (~8B params).

Using 4-bit NF4 quantization via BitsAndBytes:
- VRAM: ~5.4 GB (vs 16.2 GB at fp16)
- Quality degradation: <= 0.004 PLCC, <= 0.003 SRCC (negligible)

Custom loader bypasses pyiqa to add device_map="auto" and max_memory
constraints, preventing OOM on 8GB GPUs during weight loading.
"""

import gc
import warnings

import cv2
import numpy as np
import torch
import torch.nn as nn

from transformers import BitsAndBytesConfig, CLIPImageProcessor
import torchvision.transforms.functional as F


def _expand2square(pil_img):
    """Pad image to square (required by mPLUG-Owl2 vision encoder)."""
    from PIL import Image
    width, height = pil_img.size
    if width == height:
        return pil_img
    long_side = max(width, height)
    result = Image.new(pil_img.mode, (long_side, long_side), (0, 0, 0))
    result.paste(pil_img, ((long_side - width) // 2, (long_side - height) // 2))
    return result


class QAlignWrapper(nn.Module):
    """Lightweight wrapper around Q-Align with device_map support for 8GB GPUs."""

    def __init__(self, device: str = "cuda"):
        super().__init__()

        from pyiqa.archs.q_align.modeling_mplug_owl2 import MPLUGOwl2LlamaForCausalLM

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"The following generation flags are not valid",
            )
            self.model = MPLUGOwl2LlamaForCausalLM.from_pretrained(
                "q-future/one-align",
                trust_remote_code=True,
                quantization_config=bnb_config,
                torch_dtype=torch.float16,
                device_map="auto",
                max_memory={0: "7GiB", "cpu": "24GiB"},
                low_cpu_mem_usage=True,
                offload_buffers=True,
            )

        if getattr(self.model, "generation_config", None) is not None:
            gen_cfg = self.model.generation_config
            if not getattr(gen_cfg, "do_sample", False):
                gen_cfg.temperature = None
                gen_cfg.top_p = None

        self.image_processor = CLIPImageProcessor.from_pretrained(
            "q-future/one-align", trust_remote_code=True
        )

    def preprocess(self, x: torch.Tensor) -> torch.Tensor:
        """(1, 3, H, W) float [0,1] tensor -> model-ready image tensor."""
        pil_img = F.to_pil_image(x[0])
        pil_img = _expand2square(pil_img)
        pixel_values = self.image_processor.preprocess(pil_img, return_tensors="pt")[
            "pixel_values"
        ].to(dtype=torch.float16)
        return pixel_values.to(x.device)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        image_tensor = self.preprocess(x)
        score = self.model.score(
            images=None, image_tensor=image_tensor, task_="quality", input_="image"
        )
        return score


def load_model(device: str = "cuda"):
    """Load Q-Align 4-bit with device_map=auto for 8GB GPUs.

    Reduces concurrent loading workers to 1 to prevent OOM during
    bitsandbytes quantization (each worker needs fp16 tensor + quantized
    tensor on GPU simultaneously).
    """
    import transformers.core_model_loading as cml
    original_workers = cml.GLOBAL_WORKERS
    cml.GLOBAL_WORKERS = 1  # prevent OOM from parallel quantization
    try:
        model = QAlignWrapper(device=device)
    finally:
        cml.GLOBAL_WORKERS = original_workers
    model.eval()
    return model


def unload_model(model):
    """Aggressively free Q-Align from GPU memory.

    BitsAndBytes + device_map="auto" attaches accelerate dispatch hooks that
    prevent normal garbage collection. We must remove them explicitly.
    """
    try:
        from accelerate.hooks import remove_hook_from_submodules
        if hasattr(model, 'model'):
            remove_hook_from_submodules(model.model)
    except (ImportError, Exception):
        pass
    # Delete all sub-attributes that might hold GPU tensors
    if hasattr(model, 'model'):
        del model.model
    if hasattr(model, 'image_processor'):
        del model.image_processor
    del model
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.empty_cache()


def preprocess_frame(frame: np.ndarray) -> torch.Tensor:
    """BGR uint8 OpenCV frame -> (1, 3, H, W) float32 tensor in [0, 1]."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    t = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
    return t.unsqueeze(0)  # (1, 3, H, W)


def score_frames(
    frames: list[np.ndarray],
    model,
    device: str = "cuda",
) -> np.ndarray:
    """
    Compute per-frame quality scores using Q-Align 4-bit.

    NOTE: Q-Align only supports batch_size=1 due to its preprocess
    (expand2square + CLIPImageProcessor). Each frame is processed individually.

    Args:
        frames: list of BGR uint8 OpenCV frames
        model: QAlignWrapper
        device: cuda or cpu

    Returns:
        np.ndarray of shape (n_frames,) — quality score per frame
    """
    if not frames:
        return np.zeros(0, dtype=np.float32)

    all_scores = []
    for frame in frames:
        frame_t = preprocess_frame(frame).to(device)
        with torch.inference_mode():
            score = model(frame_t)
        all_scores.append(score.item())
        del frame_t, score

    return np.array(all_scores, dtype=np.float32)


def score_segment(frame_scores: np.ndarray) -> dict:
    """
    Compute segment-level quality features from per-frame Q-Align scores.

    Args:
        frame_scores: (N_frames,) array of per-frame quality scores

    Returns:
        dict with mean, std, min, max, median scores
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
    Rank segments in a cluster by Q-Align quality.

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
