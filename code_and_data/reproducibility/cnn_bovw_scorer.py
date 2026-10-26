"""CNN spatial features + BoVW scoring for quality benchmark.

Replaces ONLY the SIFT feature extractor with CNN spatial features.
The BoVW + TF-IDF scoring pipeline is identical — reuse run_sift_scoring_corrected()
from benchmark.py to prove only the extractor changed.

Supported models:
  resnet18      — 512-D,  7x7  = 49  descriptors/frame
  resnet50      — 2048-D, 7x7  = 49  descriptors/frame
  resnet101     — 2048-D, 7x7  = 49  descriptors/frame
  vgg16         — 512-D,  14x14 = 196 descriptors/frame
  vgg19         — 512-D,  14x14 = 196 descriptors/frame
  efficientnet  — 1280-D, 7x7  = 49  descriptors/frame
  mobilenet     — 960-D,  7x7  = 49  descriptors/frame
"""

import sys
import gc
import logging

sys.path.insert(0, "/dados/MESTRADO-USP/open-video-summary")

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms

from open_video_summary.entities.image import Keyframe
from open_video_summary.entities.video import VideoSegment
from open_video_summary.handlers.image import KeyframeHandler
from open_video_summary.utils.processing.video import VideoProcessor

log = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# Model loaders — each returns only the spatial feature extractor (no GAP/fc)
# ---------------------------------------------------------------------------

def _load_resnet18(device):
    from torchvision.models import resnet18, ResNet18_Weights
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    return nn.Sequential(*list(model.children())[:-2]).to(device).half().eval()


def _load_resnet50(device):
    from torchvision.models import resnet50, ResNet50_Weights
    model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
    return nn.Sequential(*list(model.children())[:-2]).to(device).half().eval()


def _load_resnet101(device):
    from torchvision.models import resnet101, ResNet101_Weights
    model = resnet101(weights=ResNet101_Weights.IMAGENET1K_V2)
    return nn.Sequential(*list(model.children())[:-2]).to(device).half().eval()


def _load_vgg16(device):
    from torchvision.models import vgg16, VGG16_Weights
    model = vgg16(weights=VGG16_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_vgg19(device):
    from torchvision.models import vgg19, VGG19_Weights
    model = vgg19(weights=VGG19_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_efficientnet(device):
    from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
    model = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_mobilenet(device):
    from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
    model = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    return model.features.to(device).half().eval()


def _load_convnext_tiny(device):
    from torchvision.models import convnext_tiny, ConvNeXt_Tiny_Weights
    model = convnext_tiny(weights=ConvNeXt_Tiny_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_convnext_small(device):
    from torchvision.models import convnext_small, ConvNeXt_Small_Weights
    model = convnext_small(weights=ConvNeXt_Small_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_densenet121(device):
    from torchvision.models import densenet121, DenseNet121_Weights
    model = densenet121(weights=DenseNet121_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_densenet201(device):
    from torchvision.models import densenet201, DenseNet201_Weights
    model = densenet201(weights=DenseNet201_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_resnext50(device):
    from torchvision.models import resnext50_32x4d, ResNeXt50_32X4D_Weights
    model = resnext50_32x4d(weights=ResNeXt50_32X4D_Weights.IMAGENET1K_V2)
    return nn.Sequential(*list(model.children())[:-2]).to(device).half().eval()


def _load_resnext101(device):
    from torchvision.models import resnext101_64x4d, ResNeXt101_64X4D_Weights
    model = resnext101_64x4d(weights=ResNeXt101_64X4D_Weights.IMAGENET1K_V1)
    return nn.Sequential(*list(model.children())[:-2]).to(device).half().eval()


def _load_wide_resnet50(device):
    from torchvision.models import wide_resnet50_2, Wide_ResNet50_2_Weights
    model = wide_resnet50_2(weights=Wide_ResNet50_2_Weights.IMAGENET1K_V2)
    return nn.Sequential(*list(model.children())[:-2]).to(device).half().eval()


def _load_wide_resnet101(device):
    from torchvision.models import wide_resnet101_2, Wide_ResNet101_2_Weights
    model = wide_resnet101_2(weights=Wide_ResNet101_2_Weights.IMAGENET1K_V2)
    return nn.Sequential(*list(model.children())[:-2]).to(device).half().eval()


def _load_inception_v3(device):
    from torchvision.models import inception_v3, Inception_V3_Weights
    model = inception_v3(weights=Inception_V3_Weights.IMAGENET1K_V1)
    # inception needs special handling: use Mixed_7c output
    # extract features up to last conv block
    layers = []
    for name, child in model.named_children():
        if name == "fc" or name == "AuxLogits" or name == "avgpool" or name == "dropout":
            continue
        layers.append(child)
    return nn.Sequential(*layers).to(device).half().eval()


def _load_efficientnet_b4(device):
    from torchvision.models import efficientnet_b4, EfficientNet_B4_Weights
    model = efficientnet_b4(weights=EfficientNet_B4_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_squeezenet(device):
    from torchvision.models import squeezenet1_1, SqueezeNet1_1_Weights
    model = squeezenet1_1(weights=SqueezeNet1_1_Weights.IMAGENET1K_V1)
    return model.features.to(device).half().eval()


def _load_mobilenet_v2(device):
    from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
    model = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V2)
    return model.features.to(device).half().eval()


_LOADERS = {
    "resnet18": _load_resnet18,
    "resnet50": _load_resnet50,
    "resnet101": _load_resnet101,
    "vgg16": _load_vgg16,
    "vgg19": _load_vgg19,
    "efficientnet": _load_efficientnet,
    "mobilenet": _load_mobilenet,
    "convnext_tiny": _load_convnext_tiny,
    "convnext_small": _load_convnext_small,
    "densenet121": _load_densenet121,
    "densenet201": _load_densenet201,
    "resnext50": _load_resnext50,
    "resnext101": _load_resnext101,
    "wide_resnet50": _load_wide_resnet50,
    "wide_resnet101": _load_wide_resnet101,
    "inception_v3": _load_inception_v3,
    "efficientnet_b4": _load_efficientnet_b4,
    "squeezenet": _load_squeezenet,
    "mobilenet_v2": _load_mobilenet_v2,
}

ALL_CNN_NAMES = list(_LOADERS.keys())


def load_model(name: str, device: str = "cuda") -> nn.Module:
    log.info(f"Loading {name} (spatial features) for BoVW...")
    return _LOADERS[name](device)


def unload_model(model: nn.Module):
    model.cpu()
    del model
    gc.collect()
    torch.cuda.empty_cache()


# ---------------------------------------------------------------------------
# Feature extraction — produces same format as extract_sift_features()
# ---------------------------------------------------------------------------

def _forward_sem_nan(model, batch):
    """⛔ 21/09/2026: NENHUM DESCRITOR NaN SAI DAQUI EM SILENCIO.

    MobileNet-V3-Large em fp16 devolve 100 % de NaN neste ambiente
    (torch 2.11 + cu130, RTX 4060) para QUALQUER lote maior que 1, e 0 % com lote 1.
    A ablacao roda com lote 32, entao aquele extrator saia inteiramente NaN, e o
    `num_matches` do filtro de quadro-chave virava 0 — o que faz TODO quadro virar
    keyframe por aritmetica invalida, nao por propriedade do filtro.

    ⚠️ Os valores ARQUIVADOS daquele extrator sao finitos, entao o ambiente em que a
    rodada publicada aconteceu nao tinha este comportamento. Isto e falha de REPRODUCAO
    no ambiente atual, nao defeito do numero publicado.

    A causa e a selecao de kernel do cuDNN: com `cudnn.enabled = False` o mesmo fp16
    volta a sair limpo, e mais perto da referencia (lote 1, fp16) do que ir para fp32:
    erro relativo medio 4,1e-3 contra 6,0e-3. Por isso o primeiro recuo e desligar o
    cuDNN e NAO trocar a precisao — mexer em precisao mudaria a numerica de todo mundo.

    ⭐ E o caminho normal fica INTACTO: para um modelo que nao produz NaN, esta funcao e
    um `if` a mais. So quem quebra paga o recuo.
    """
    saida = model(batch)
    if not torch.isnan(saida).any():
        return saida
    aviso = "%s: fp16 devolveu NaN no lote de %d" % (
        getattr(model, "_nome_arquitetura", "modelo"), len(batch))
    antes = torch.backends.cudnn.enabled
    try:
        torch.backends.cudnn.enabled = False
        saida = model(batch)
    finally:
        torch.backends.cudnn.enabled = antes
    if not torch.isnan(saida).any():
        log.warning("%s; refeito com cuDNN desligado", aviso)
        return saida
    saida = model.float()(batch.float())
    if torch.isnan(saida).any():
        raise RuntimeError(
            "%s, e nem cuDNN desligado nem fp32 resolveram. NAO devolvo descritor NaN: "
            "ele faria o filtro de quadro-chave aceitar todo quadro por aritmetica "
            "invalida e o numero sairia sem nada acusar." % aviso)
    log.warning("%s; refeito em fp32", aviso)
    return saida


def extract_features(
    cluster: set[VideoSegment],
    model: nn.Module,
    device: str = "cuda",
    batch_size: int = 32,
    use_keyframe_filter: bool = True,
) -> dict[VideoSegment, np.ndarray]:
    """Extract CNN spatial features for each segment in a cluster.

    Returns dict[VideoSegment, (N, D)] — same format as SIFT features.
    The BoVW + TF-IDF scoring functions work identically on this output.
    """
    transform = build_transform()
    seg_features: dict[VideoSegment, np.ndarray] = {}

    for segment in cluster:
        frames = VideoProcessor.retrieve_video_frames(
            segment.video_path,
            grayscale=False,
            start_second=segment.start,
            end_second=segment.end,
        )
        if len(frames) < 3:
            continue

        # preprocess all frames
        tensors = torch.stack([
            transform(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames
        ])

        # extract spatial features in batches -> per-frame (H*W, C) descriptors
        per_frame_descs: list[np.ndarray] = []
        with torch.inference_mode():
            for i in range(0, len(tensors), batch_size):
                batch = tensors[i : i + batch_size].to(device).half()
                spatial = _forward_sem_nan(model, batch)  # (B, C, H, W)
                B, C, H, W = spatial.shape
                # float32 before normalize to avoid fp16 NaN/overflow
                descs = spatial.float().permute(0, 2, 3, 1).reshape(B, H * W, C)
                descs = torch.nn.functional.normalize(descs, p=2, dim=2)
                for d in descs.cpu().numpy():
                    per_frame_descs.append(d)
                del batch, spatial, descs

        # keyframe filtering — identical to ImageProcessor.ks_sift logic
        if use_keyframe_filter and len(per_frame_descs) > 2:
            segment_keyframes: list[Keyframe] = []
            for desc in per_frame_descs[1:-1]:  # skip first/last like ks_sift
                kf = Keyframe(descriptor=desc)
                if KeyframeHandler.is_keyframe(kf, segment_keyframes):
                    segment_keyframes.append(kf)
            if segment_keyframes:
                seg_features[segment] = np.concatenate(
                    [kf.descriptor for kf in segment_keyframes]
                )
                continue

        # fallback: all frames (no filter or all filtered out)
        if per_frame_descs:
            seg_features[segment] = np.concatenate(per_frame_descs, axis=0)

    return seg_features
