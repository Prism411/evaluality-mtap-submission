"""Minimal, reproducible wrapper around the official DOVER technical branch."""

from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
import torch
import yaml


HERE = Path(__file__).resolve().parent
DOVER_ROOT = HERE / "vendor" / "DOVER"
DEPS = HERE / "vendor" / "python-deps"
sys.path.insert(0, str(DEPS))
sys.path.insert(0, str(DOVER_ROOT))

from dover.datasets import UnifiedFrameSampler, spatial_temporal_view_decomposition  # noqa: E402
from dover.models import DOVER  # noqa: E402


MEAN = torch.FloatTensor([123.675, 116.28, 103.53])
STD = torch.FloatTensor([58.395, 57.12, 57.375])


class DoverTechnical:
    def __init__(self, device: str = "cuda", seed: int = 42):
        self.device = torch.device(device)
        self.seed = seed
        config = yaml.safe_load(open(DOVER_ROOT / "dover.yml"))
        self.model = DOVER(**config["model"]["args"]).to(self.device)
        checkpoint = DOVER_ROOT / "pretrained_weights" / "DOVER.pth"
        state = torch.load(checkpoint, map_location=self.device, weights_only=False)
        self.model.load_state_dict(state)
        self.model.eval()
        self.options = config["data"]["val-l1080p"]["args"]["sample_types"]["technical"]
        self.sampler = UnifiedFrameSampler(
            self.options["clip_len"],
            self.options["num_clips"],
            self.options["frame_interval"],
        )

    def _seed(self) -> None:
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

    def score(self, video_path: Path) -> float:
        self._seed()
        views, _ = spatial_temporal_view_decomposition(
            str(video_path),
            {"technical": self.options},
            {"technical": self.sampler},
        )
        value = views["technical"]
        clips = self.options.get("num_clips", 1)
        tensor = (
            ((value.permute(1, 2, 3, 0) - MEAN) / STD)
            .permute(3, 0, 1, 2)
            .reshape(value.shape[0], clips, -1, *value.shape[2:])
            .transpose(0, 1)
            .to(self.device)
        )
        with torch.inference_mode():
            output = self.model({"technical": tensor})[0]
        result = float(output.mean().item())
        del views, value, tensor, output
        return result

