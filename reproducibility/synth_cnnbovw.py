"""P4: the 19 CNN+BoVW variants on the constructed ground truth.

The pre-registered prediction is that all 19 sit at the chance floor on every
degradation type, because a fixed-size feature map holds D_i constant and so
switches off the count channel of Equation (8), leaving only the bounded rarity
channel. This is the load-bearing counterfactual: if the variants do *not* sit
at chance, the rarity channel carries something after all and the factorization
argument collapses.

The pipeline is identical to synth_sift.py except for the descriptor extractor:
keyframes are selected by the deployed selector (ks_sift), the vocabulary is fit
per pair with N = 2 documents, and the score is the same TF-IDF sum. Only the
descriptors change, which is what makes this an ablation rather than a different
experiment.
"""
import sys, json, os, time
from math import log10
from collections import Counter
from pathlib import Path

import numpy as np
import cv2
from sklearn.cluster import KMeans

ROOT = Path("/dados/Projetos/quality-benchmark")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "/dados/MESTRADO-USP/open-video-summary")
os.chdir(ROOT)
import cnn_bovw_scorer as cbs
from open_video_summary.utils.processing.image import ImageProcessor

# ⛔ este caminho era um SCRATCHPAD de sessao antiga, que nao existe mais para ninguem,
# nem para o autor: o script publicado nao rodava em lugar nenhum.
HERE = Path(__file__).resolve().parent
if not (HERE / "synth_sift.json").exists() and (HERE / "derived_data").exists():
    HERE = HERE / "derived_data"
SYN = HERE / "synth_frames"
OUT = HERE / "synth_cnnbovw.json"
K = 300

ARCHS = ["resnet18", "resnet50", "resnet101", "vgg16", "vgg19", "efficientnet",
         "mobilenet", "convnext_tiny", "convnext_small", "densenet121",
         "densenet201", "resnext50", "resnext101", "wide_resnet50",
         "wide_resnet101", "inception_v3", "efficientnet_b4", "squeezenet",
         "mobilenet_v2"]

sift = json.load(open(HERE / "synth_sift.json"))
full = sorted(sift["_subset"])
# 19 architectures x 800 pairs would take about 30 hours, dominated by K-means
# in 2048 dimensions. P4 is registered over all 19 architectures, so the
# architecture axis is kept complete and the segment axis is halved instead:
# 10 of the 20, drawn with the same generator seed. Intervals widen; the
# prediction is unchanged.
subset = sorted(np.random.default_rng(42).choice(full, size=10, replace=False).tolist())
print(f"{len(ARCHS)} architectures x {len(subset)} segments", flush=True)
for s in subset:
    print(f"    {s}", flush=True)

res = json.load(open(OUT)) if OUT.exists() else {}


def save():
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(res, f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(OUT)


def frames_of(seg, cond):
    d = SYN / seg / cond
    return [cv2.imread(str(p)) for p in sorted(d.glob("*.png"))]


tr = cbs.build_transform()
import torch
from open_video_summary.entities.image import Keyframe
from open_video_summary.handlers.image import KeyframeHandler

for arch in ARCHS:
    if arch in res:
        print(f"[skip] {arch}", flush=True)
        continue
    t0 = time.time()
    try:
        model = cbs.load_model(arch, device="cuda")
    except Exception as e:
        print(f"[ERR] {arch}: {type(e).__name__}: {e}", flush=True)
        continue

    def feats(seg, cond):
        """Exactly the body of cnn_bovw_scorer.extract_features, reading PNGs
        instead of a video file. Same L2 normalization, same keyframe filter,
        same first/last frame exclusion, so only the input source differs."""
        fr = frames_of(seg, cond)
        if len(fr) < 3:
            return None
        tensors = torch.stack([tr(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in fr])
        per_frame = []
        with torch.inference_mode():
            for i in range(0, len(tensors), 16):
                batch = tensors[i:i + 16].to("cuda").half()
                spatial = model(batch)
                B, C, H, W = spatial.shape
                descs = spatial.float().permute(0, 2, 3, 1).reshape(B, H * W, C)
                descs = torch.nn.functional.normalize(descs, p=2, dim=2)
                per_frame.extend(descs.cpu().numpy())
                del batch, spatial, descs
        if len(per_frame) > 2:
            kfs = []
            for desc in per_frame[1:-1]:
                kf = Keyframe(descriptor=desc)
                if KeyframeHandler.is_keyframe(kf, kfs):
                    kfs.append(kf)
            if kfs:
                return np.concatenate([k.descriptor for k in kfs]).astype(np.float32)
        return np.concatenate(per_frame, axis=0).astype(np.float32)

    per_arch = {}
    for seg in subset:
        fb = feats(seg, "orig")
        if fb is None:
            continue
        for c in sorted((SYN / seg).iterdir()):
            if not c.is_dir() or c.name == "orig":
                continue
            fd = feats(seg, c.name)
            if fd is None:
                continue
            pool = np.concatenate([fb, fd])
            k_eff = K if len(pool) >= K else max(2, len(pool) // 2)
            try:
                km = KMeans(n_clusters=k_eff, random_state=42, n_init=1).fit(pool)
                tf = {"orig": Counter(km.predict(fb)), "deg": Counter(km.predict(fd))}
            except Exception as e:
                print(f"  ! {arch}/{seg}/{c.name}: {type(e).__name__}", flush=True)
                continue
            df = Counter(w for x in tf.values() for w in x)
            sc = {nm: sum(n * log10(k_eff / df[w]) for w, n in x.items())
                  for nm, x in tf.items()}
            per_arch[f"{seg}|{c.name}"] = {
                "orig": sc["orig"], "deg": sc["deg"],
                "n_orig": int(len(fb)), "n_deg": int(len(fd)), "K": k_eff}
            print(f"    {arch:<16} {seg[:26]:<28} {c.name:<10} "
                  f"D={len(fb)}/{len(fd)} {time.time()-t0:.0f}s", flush=True)
        print(f"  {arch}: {seg[:30]:<32} done ({time.time()-t0:.0f}s)", flush=True)

    res[arch] = per_arch
    save()
    print(f"[ok] {arch}: {len(per_arch)} pairs in {(time.time()-t0)/60:.1f} min", flush=True)
    cbs.unload_model(model)
    torch.cuda.empty_cache()

print("FIM cnnbovw", flush=True)

