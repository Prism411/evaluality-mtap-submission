#!/usr/bin/env python3
"""⭐⭐ O FILTRO DE QUADRO-CHAVE NOS TRES REGIMES DE DESCRITOR.

POR QUE EXISTE (21/09/2026). Ao tentar pôr o ORB na ablacao de descritores, o filtro de
quadro-chave do sistema implantado degenerou: 1 de 28 quadros com SIFT contra 28 de 28 com
ORB. ⛔ Ficou declarado que aquilo NAO dizia nada sobre as 19 CNNs, que passam pelo mesmo
filtro. **Esta rodada responde essa pergunta, em vez de fechar por analogia.**

⭐ E LENDO O CODIGO APARECEU A RAZAO DE HAVER TRES REGIMES, nao dois. O
`cnn_bovw_scorer.extract_features` faz `torch.nn.functional.normalize(descs, p=2, dim=2)`:
os descritores da CNN sao UNITARIOS, entao o produto escalar e COSSENO em [-1, 1] e o
limiar 0,95 do `num_matches` e um limiar de cosseno, que e o que ele parece ser. ⛔ O SIFT
(`float32` cru) e o ORB (`uint8`) NAO sao normalizados: os produtos ficam na casa de 10^5 e
o `>= 0,95` e sempre verdadeiro, ou seja o limiar nao filtra nada nesses dois.

A PERGUNTA: com o limiar funcionando como cosseno, quantos quadros a CNN seleciona?

⛔ CRITERIO DECLARADO ANTES DE RODAR. Tres desfechos possiveis, e os tres sao publicaveis:
  A) a CNN seleciona ~todos, como o ORB  -> a degeneracao e PRE-EXISTENTE na ablacao
     publicada, e a frase do artigo sobre os 19 extratores precisa de ressalva;
  B) a CNN seleciona ~1, como o SIFT     -> o ORB e o caso desviante e o achado e dele;
  C) a CNN fica no meio                  -> o filtro responde a escala, e os tres regimes
     sao tres pontos de um mesmo eixo, que e a leitura mais forte.
"""
import glob
import json
import sys
import time

sys.path.insert(0, '/data/projects/benchmark')
sys.path.insert(0, '/dados/MESTRADO-USP/open-video-summary')

import cv2                                                           # noqa: E402
import numpy as np                                                   # noqa: E402
import torch                                                         # noqa: E402
import casamento_rapido as CR                                        # noqa: E402
import cnn_bovw_scorer as cbs                                        # noqa: E402
from open_video_summary.entities.image import Keyframe               # noqa: E402
from open_video_summary.handlers.image import KeyframeHandler as KH  # noqa: E402

N_QUADROS = 28
ARQUITETURAS = ['resnet50', 'vgg16', 'mobilenet']
SAIDA = '/data/projects/benchmark/o_filtro_nos_tres_regimes.json'


def _passa(descs, nome):
    """O mesmo filtro, sobre a lista de descritores por quadro que o regime produz."""
    sel, mat, lim, prod = [], [], [], []
    t = time.perf_counter()
    for d in descs:
        kf = Keyframe(descriptor=np.ascontiguousarray(d, dtype=np.float32))
        if sel:
            mat.append(int(KH.num_matches(kf, sel[-1])))
            lim.append(float(0.1 * sel[-1].descriptor_size))
            prod.append(float(kf.descriptor[0] @ sel[-1].descriptor[0]))
        if KH.is_keyframe(kf, sel):
            sel.append(kf)
    return {'regime': nome, 'quadros': len(descs), 'viram_keyframe': len(sel),
            'descritores_por_quadro': int(len(descs[0])),
            'descritores_totais': int(sum(len(k.descriptor) for k in sel)),
            'produto_escalar_tipico': round(float(np.median(prod)), 4) if prod else None,
            'normalizado': bool(prod and abs(np.median(prod)) <= 1.0),
            'num_matches_mediano': int(np.median(mat)) if mat else None,
            'limiar_de_is_keyframe': round(float(np.median(lim)), 1) if lim else None,
            'segundos': round(time.perf_counter() - t, 1)}


def main():
    CR.instala()
    cap = cv2.VideoCapture(sorted(glob.glob(
        '/data/projects/platform/data/dataset/*/*.mp4'))[0])
    bgr = []
    for _ in range(N_QUADROS):
        ok, f = cap.read()
        if not ok:
            break
        bgr.append(f)
    cap.release()
    cinza = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in bgr]

    linhas = []
    for nome, det in (('SIFT (float32 cru, 128-D)', cv2.SIFT_create()),
                      ('ORB (uint8, 32-B)', cv2.ORB_create(nfeatures=20000))):
        ds = [det.detectAndCompute(f, None)[1] for f in cinza]
        ds = [d for d in ds if d is not None]
        linhas.append(_passa(ds, nome))

    # ⭐ as CNNs, pelo MESMO caminho do `extract_features`: mapa espacial achatado e
    # L2-normalizado por descritor, que e o que faz o limiar 0,95 virar cosseno.
    tr = cbs.build_transform()
    tensores = torch.stack([tr(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in bgr])
    for arq in ARQUITETURAS:
        modelo = cbs.load_model(arq, device='cuda')
        modelo._nome_arquitetura = arq
        descs = []
        with torch.inference_mode():
            for i in range(0, len(tensores), 16):
                b = tensores[i:i + 16].to('cuda').half()
                # ⭐ passa pela guarda de NaN: sem ela a mobilenet saia 100 % NaN e o
                # filtro aceitava todo quadro por aritmetica invalida
                esp = cbs._forward_sem_nan(modelo, b)
                B, C, H, W = esp.shape
                d = esp.float().permute(0, 2, 3, 1).reshape(B, H * W, C)
                d = torch.nn.functional.normalize(d, p=2, dim=2)
                descs += [x for x in d.cpu().numpy()]
        cbs.unload_model(modelo)
        linhas.append(_passa(descs, f'{arq} (L2-normalizado, {descs[0].shape[1]}-D)'))

    # ⛔ UM REGIME COM DESCRITOR NaN NAO CONTA COMO DEGENERACAO DO FILTRO. A primeira
    # rodada deu «C» porque a mobilenet selecionou 28 de 28 — mas o produto escalar dela
    # saiu NaN, entao `num_matches` foi 0 e TUDO virou keyframe por aritmetica invalida,
    # nao por escala. Rotular aquilo de degeneracao seria o rotulo afirmando mais do que o
    # bloco testou. Os NaN saem do veredito e vao declarados a parte.
    cnn = [x for x in linhas if 'normalizado' in x['regime']]
    nan = [x for x in cnn if x['produto_escalar_tipico'] is None
           or x['produto_escalar_tipico'] != x['produto_escalar_tipico']]
    validas = [x for x in cnn if x not in nan]
    if not validas:
        desfecho = 'INDECIDIVEL: nenhuma CNN produziu descritor valido neste ambiente'
    else:
        todos = all(x['viram_keyframe'] >= 0.9 * x['quadros'] for x in validas)
        um = all(x['viram_keyframe'] <= 2 for x in validas)
        desfecho = ('A: a degeneracao e PRE-EXISTENTE na ablacao publicada' if todos else
                    'B: as CNNs validas NAO degeneram; o caso desviante e o descritor '
                    'binario, por ESCALA' if um else
                    'C: o filtro responde a escala e os regimes sao pontos de um eixo')
    out = {'_o_que_e': __doc__.strip(), 'limiar_do_num_matches': 0.95,
           'por_regime': linhas,
           '🔴_regimes_com_descritor_NaN': [x['regime'] for x in nan],
           '⚠️_por_que_os_NaN_saem_do_veredito': (
               'descritor NaN faz num_matches = 0 e TODO quadro vira keyframe por '
               'aritmetica invalida, nao por propriedade do filtro'),
           '⭐_DESFECHO': desfecho}
    json.dump(out, open(SAIDA, 'w'), indent=1, ensure_ascii=False)
    print(f"\n  {'regime':38s} {'kf':>7s} {'desc/quadro':>12s} {'produto':>12s} "
          f"{'matches':>8s} {'limiar':>8s}")
    for x in linhas:
        print(f"  {x['regime']:38s} {x['viram_keyframe']:3d}/{x['quadros']:<3d} "
              f"{x['descritores_por_quadro']:12d} {str(x['produto_escalar_tipico']):>12s} "
              f"{str(x['num_matches_mediano']):>8s} {str(x['limiar_de_is_keyframe']):>8s}")
    print(f"\n  ⭐ DESFECHO — {desfecho}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
