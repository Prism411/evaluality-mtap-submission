#!/usr/bin/env python3
"""Score KADID-10k with a pyiqa model and persist per-image scores.

The manuscript reanalysis needs the per-image values so that distortion-level
sensitivity can be computed within each of the 81 reference images.  The
original aggregate JSON is insufficient for that calculation.

Example
-------
python score_pyiqa_kadid_cache.py --model clipiqa+ --output-name clipiqa_plus
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image
import pyiqa
import torch
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms.functional import to_tensor


PROJECT_DIR = Path(__file__).resolve().parent
METADATA = PROJECT_DIR / "data" / "kadid10k" / "kadid10k" / "dmos.csv"
IMAGES = PROJECT_DIR / "data" / "kadid10k" / "kadid10k" / "images"
OUTPUT_DIR = PROJECT_DIR / "results" / "kadid10k" / "scores_cache"


class KadidImages(Dataset):
    def __init__(self, image_names: list[str]) -> None:
        self.image_names = image_names

    def __len__(self) -> int:
        return len(self.image_names)

    def __getitem__(self, index: int) -> tuple[str, torch.Tensor]:
        name = self.image_names[index]
        with Image.open(IMAGES / name) as image:
            tensor = to_tensor(image.convert("RGB"))
        return name, tensor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="pyiqa model name")
    parser.add_argument(
        "--output-name",
        required=True,
        help="cache filename stem, for example clipiqa_plus",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not METADATA.is_file() or not IMAGES.is_dir():
        raise FileNotFoundError("KADID metadata or image directory is missing")

    names = pd.read_csv(METADATA)["dist_img"].tolist()
    output = OUTPUT_DIR / f"{args.output_name}.csv"
    if output.exists():
        cached = pd.read_csv(output)
        if cached["image_name"].tolist() == names and len(cached) == len(names):
            print(f"Complete cache already exists: {output}")
            return
        raise RuntimeError(f"Refusing to overwrite incomplete or mismatched cache: {output}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    metric = pyiqa.create_metric(args.model, device=device)
    loader = DataLoader(
        KadidImages(names),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        pin_memory=device == "cuda",
    )

    scored_names: list[str] = []
    scores: list[float] = []
    with torch.inference_mode():
        for batch_number, (batch_names, images) in enumerate(loader, start=1):
            values = metric(images.to(device, non_blocking=True))
            scored_names.extend(batch_names)
            scores.extend(values.detach().cpu().reshape(-1).tolist())
            if batch_number % 25 == 0:
                print(f"scored {len(scores)}/{len(names)}")

    if scored_names != names or len(scores) != len(names):
        raise RuntimeError("Scored output does not match KADID metadata order")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"image_name": names, "score": scores}).to_csv(output, index=False)
    print(f"wrote {len(scores)} scores to {output}")


if __name__ == "__main__":
    main()
