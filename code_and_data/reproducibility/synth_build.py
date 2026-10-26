"""Build the synthetic in-domain ground truth: 83 segments x 8 degradations x 5
levels, from the frames already cached. Predictions registered in the benchmark
repository at commit 9377c07 before this ran.

Two degradation families. The KADID-compatible four make the result comparable
with Axis 1 and with the literature; the broadcast-realistic four are the
degradation paths that actually distinguish one broadcaster's feed from
another's and that KADID does not contain.
"""
import json, subprocess, tempfile
from pathlib import Path

import numpy as np
import cv2

HERE = Path(__file__).resolve().parent
CACHE = HERE / "e2e_frames"
OUT = HERE / "synth_frames"
OUT.mkdir(exist_ok=True)
CAP = 30           # frames per segment, uniform subsample
LEVELS = 5

# every distinct segment with a cached frame set: the 83 of the automatic
# cluster set, which is 2.7x the annotated set and gives designs A and B more
# power. Design C additionally needs the overlay annotation and is restricted
# to the segments that carry one.
segs = {d.name: d for d in sorted(CACHE.iterdir()) if d.is_dir() and any(d.glob("*.png"))}
print(f"{len(segs)} distinct segments with cached frames", flush=True)


def load(d):
    ps = sorted(d.glob("*.png"))
    if len(ps) > CAP:
        idx = np.linspace(0, len(ps) - 1, CAP).round().astype(int)
        ps = [ps[i] for i in idx]
    return [cv2.imread(str(p)) for p in ps]


# ---- degradations: f(img, level 1..5) -> img -----------------------------
def blur(im, L):
    k = [3, 5, 9, 15, 23][L - 1]
    return cv2.GaussianBlur(im, (k, k), 0)


def noise(im, L):
    s = [5, 12, 22, 35, 50][L - 1]
    n = np.random.default_rng(1000 + L).normal(0, s, im.shape)
    return np.clip(im.astype(np.float32) + n, 0, 255).astype(np.uint8)


def dark(im, L):
    g = [0.80, 0.62, 0.46, 0.32, 0.20][L - 1]
    return np.clip(im.astype(np.float32) * g, 0, 255).astype(np.uint8)


def jpeg(im, L):
    q = [40, 25, 15, 9, 5][L - 1]
    ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR) if ok else im


def rescale(im, L):
    f = [0.75, 0.55, 0.40, 0.28, 0.18][L - 1]
    h, w = im.shape[:2]
    small = cv2.resize(im, (max(2, int(w * f)), max(2, int(h * f))), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def motion(im, L):
    k = [5, 9, 15, 23, 33][L - 1]
    ker = np.zeros((k, k), np.float32)
    ker[k // 2, :] = 1.0 / k
    return cv2.filter2D(im, -1, ker)


def satur(im, L):
    f = [0.75, 0.55, 0.35, 0.18, 0.05][L - 1]
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] *= f
    return cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)


SPATIAL = {"blur": blur, "noise": noise, "dark": dark, "jpeg": jpeg,
           "rescale": rescale, "motion": motion, "satur": satur}
# h264 is applied to the whole frame sequence, not per frame
CRF = [30, 36, 41, 45, 50]


def h264(frames, L):
    """Encode the frame sequence at low bitrate and decode it back."""
    if not frames:
        return frames
    h, w = frames[0].shape[:2]
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.mp4"
        dst = Path(td) / "out.mp4"
        vw = cv2.VideoWriter(str(src), cv2.VideoWriter_fourcc(*"mp4v"), 5, (w, h))
        for f in frames:
            vw.write(f)
        vw.release()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                        "-c:v", "libx264", "-crf", str(CRF[L - 1]),
                        "-preset", "veryfast", str(dst)], check=True)
        cap = cv2.VideoCapture(str(dst))
        out = []
        while True:
            ok, im = cap.read()
            if not ok:
                break
            out.append(im)
        cap.release()
    return out if len(out) == len(frames) else frames


done = 0
for tag, d in segs.items():
    fr = load(d)
    if not fr:
        continue
    o = OUT / tag / "orig"
    if not o.exists():
        o.mkdir(parents=True)
        for i, f in enumerate(fr):
            cv2.imwrite(str(o / f"{i:03d}.png"), f)
    for name, fn in SPATIAL.items():
        for L in range(1, LEVELS + 1):
            dd = OUT / tag / f"{name}_{L}"
            if dd.exists():
                continue
            dd.mkdir(parents=True)
            for i, f in enumerate(fr):
                cv2.imwrite(str(dd / f"{i:03d}.png"), fn(f, L))
    for L in range(1, LEVELS + 1):
        dd = OUT / tag / f"h264_{L}"
        if dd.exists():
            continue
        enc = h264(fr, L)
        dd.mkdir(parents=True)
        for i, f in enumerate(enc):
            cv2.imwrite(str(dd / f"{i:03d}.png"), f)
    done += 1
    print(f"  [{done}/{len(segs)}] {tag}", flush=True)

n = sum(1 for _ in OUT.rglob("*.png"))
print(f"FIM: {n} frames written", flush=True)
