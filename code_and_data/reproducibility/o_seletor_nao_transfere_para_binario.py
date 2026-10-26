#!/usr/bin/env python3
"""🔴 O SELETOR DE QUADRO-CHAVE DO IMPLANTADO NAO TRANSFERE PARA DESCRITOR BINARIO.

POR QUE EXISTE (21/09/2026). Pondo o ORB na ablacao de descritores, a rodada ficou lenta
demais para o custo esperado. Investigando, a causa nao era volume: era que o filtro de
quadro-chave DEGENERA.

⛔ E O MECANISMO NAO E O QUE EU SUPUS NA PRIMEIRA LEITURA. Eu tinha escrito que o limiar
absoluto de 0,95 sobre produto escalar «passa a valer sempre» com `uint8`. Isso e verdade
mas NAO e a causa: o que decide e o `is_keyframe`, que exige
`num_matches < 0.1 * descriptor_size`, e os DOIS lados andam na direcao errada ao mesmo
tempo. Medido em 28 quadros consecutivos do corpus:

    SIFT: 692 casamentos contra limiar  85,3  ->  692 > 85,3  -> NAO e keyframe ->  1 de 28
    ORB :  75 casamentos contra limiar 318,9  ->   75 < 318,9 ->  E  keyframe    -> 28 de 28

O ORB casa MENOS entre quadros vizinhos (75 contra 692) e ao mesmo tempo tem MAIS
descritores, o que SOBE o limiar (318,9 contra 85,3). Cada quadro parece novo.

⛔ CONSEQUENCIA PARA A ABLACAO: comparar SIFT com ORB nesse caminho NAO e «so o extrator
mudou». A diferenca de contagem de descritores vem do FILTRO, que e o estagio ANTERIOR ao
escore. Rodar assim e reportar acuracia seria publicar um numero cujo eixo esta quebrado.

⭐ ESTE E O RESULTADO, e ele responde ao pedido do orientador melhor que um numero: a
operacao da classe 2 NAO e plugavel por troca de descritor quando o descritor e binario,
porque o estagio anterior a ela depende da ESCALA do descritor.

⚠️ O QUE ISTO NAO DIZ: nada sobre as 19 CNNs. Elas tambem passam por este filtro, e se
degeneram do mesmo jeito isso e propriedade PRE-EXISTENTE da ablacao publicada, nao do ORB.
Fica declarado como pergunta aberta, nao respondida aqui.
"""
import glob
import json
import sys
import time

sys.path.insert(0, '/data/projects/benchmark')
sys.path.insert(0, '/dados/MESTRADO-USP/open-video-summary')

import cv2                                                        # noqa: E402
import numpy as np                                                # noqa: E402
import casamento_rapido as CR                                     # noqa: E402
from open_video_summary.entities.image import Keyframe            # noqa: E402
from open_video_summary.handlers.image import KeyframeHandler as KH   # noqa: E402

N_QUADROS = 28
SAIDA = '/data/projects/benchmark/o_seletor_nao_transfere_para_binario.json'


def mede(fr, det, nome):
    sel, t = [], time.perf_counter()
    prod, mat, lim = [], [], []
    for f in fr:
        d = det.detectAndCompute(f, None)[1]
        if d is None:
            continue
        kf = Keyframe(descriptor=d.astype(np.float32))
        if sel:
            mat.append(int(KH.num_matches(kf, sel[-1])))
            lim.append(float(0.1 * sel[-1].descriptor_size))
            prod.append(float(kf.descriptor[0] @ sel[-1].descriptor[0]))
        if KH.is_keyframe(kf, sel):
            sel.append(kf)
    return {'extrator': nome, 'quadros': len(fr), 'viram_keyframe': len(sel),
            'descritores_totais': int(sum(len(k.descriptor) for k in sel)),
            'produto_escalar_tipico': round(float(np.median(prod)), 1) if prod else None,
            'num_matches_mediano': int(np.median(mat)) if mat else None,
            'limiar_de_is_keyframe': round(float(np.median(lim)), 1) if lim else None,
            'segundos': round(time.perf_counter() - t, 1)}


def main():
    CR.instala()
    cap = cv2.VideoCapture(sorted(glob.glob(
        '/data/projects/platform/data/dataset/*/*.mp4'))[0])
    fr = []
    for _ in range(N_QUADROS):
        ok, f = cap.read()
        if not ok:
            break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    cap.release()
    out = {'_o_que_e': __doc__.strip(),
           'limiar_absoluto_do_num_matches': 0.95,
           'por_extrator': [mede(fr, cv2.SIFT_create(), 'SIFT (float32, 128-D)'),
                            mede(fr, cv2.ORB_create(nfeatures=20000),
                                 'ORB (uint8, 32-B)')]}
    a, b = out['por_extrator']
    out['razao_de_descritores'] = round(b['descritores_totais'] /
                                        max(a['descritores_totais'], 1), 1)
    out['⚠️_o_que_isto_NAO_diz'] = ('nada sobre as 19 CNNs: elas passam pelo mesmo filtro e '
                                   'se degeneram igual isso e propriedade pre-existente da '
                                   'ablacao publicada. Pergunta aberta, nao respondida aqui.')
    out['⭐_leitura'] = (
        f"{a['extrator']} seleciona {a['viram_keyframe']} de {a['quadros']} quadros e "
        f"{b['extrator']} seleciona {b['viram_keyframe']} de {b['quadros']}: o filtro "
        f"degenera e a contagem de descritores difere por {out['razao_de_descritores']}x, "
        "pelo ESTAGIO ANTERIOR e nao pelo descritor. A ablacao por troca de extrator nao "
        "tem eixo limpo para descritor binario sem recalibrar esse estagio.")
    json.dump(out, open(SAIDA, 'w'), indent=1, ensure_ascii=False)
    for e in out['por_extrator']:
        print(f"  {e['extrator']:24s} {e['viram_keyframe']:3d}/{e['quadros']} keyframes, "
              f"{e['descritores_totais']:7d} desc, produto tipico "
              f"{e['produto_escalar_tipico']}, matches {e['num_matches_mediano']} "
              f"contra limiar {e['limiar_de_is_keyframe']}", flush=True)
    print(f"\n  razao de descritores: {out['razao_de_descritores']}x")
    return 0


if __name__ == '__main__':
    sys.exit(main())
