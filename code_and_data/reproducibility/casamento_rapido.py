#!/usr/bin/env python3
"""⭐ O `num_matches` do sistema implantado, vetorizado e PROVADO IDENTICO.

POR QUE EXISTE (21/09/2026). Ao pôr o ORB na ablação de descritores, o gargalo não era a
extração: era o filtro de quadro-chave. Uma condição levava **215,9 s** com SIFT e mais com
ORB, o que daria ~25 h para a amostra. ⛔ Cortar a amostra é legítimo e foi declarado no
pré-registro; **mexer no método para ganhar tempo não é**.

O QUE ESTA FUNÇÃO É. Exatamente a mesma conta do
`KeyframeHandler.num_matches`: vizinho-mais-próximo MÚTUO sob produto escalar, com os dois
sentidos acima do limiar. O original faz um laço em Python com um `argsort` por descritor;
aqui é uma multiplicação de matriz e dois `argmax`. ⭐ **Mesma saída, não uma aproximação.**

⚠️ O PONTO DELICADO SÃO OS EMPATES. O original usa `argsort(-sim)[0]`, que com `quicksort`
não é estável; o `argmax` devolve o PRIMEIRO máximo. Com `float` de SIFT o empate é
improvável, mas com `uint8` do ORB convertido é **plausível**. Por isso esta função não é
usada por confiança: o `confere()` abaixo roda as duas sobre descritores REAIS, de SIFT e
de ORB, e só libera se baterem em todos os pares testados.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, '/dados/MESTRADO-USP/open-video-summary')
from open_video_summary.handlers.image import KeyframeHandler   # noqa: E402


def num_matches_rapido(kf, other, threshold: float = 0.95) -> int:
    """Vizinho-mais-próximo mútuo sob produto escalar, sem laço em Python."""
    d1 = np.ascontiguousarray(kf.descriptor, dtype=np.float32)
    d2 = np.ascontiguousarray(other.descriptor, dtype=np.float32)
    if d1.size == 0 or d2.size == 0:
        return 0
    S = d1 @ d2.T                       # (n1, n2), a mesma matriz de similaridade
    j = S.argmax(axis=1)                # para cada i, o melhor j
    i_de_volta = S.argmax(axis=0)       # para cada j, o melhor i
    linhas = np.arange(len(d1))
    melhor = S[linhas, j]
    volta = S[i_de_volta[j], j]
    ok = (melhor >= threshold) & (volta >= threshold) & (i_de_volta[j] == linhas)
    return int(ok.sum())


def confere(pares, verboso=True):
    """⛔ Roda as DUAS sobre descritores reais e exige igualdade em todos os pares."""
    class _K:
        def __init__(self, d):
            self.descriptor = d
    ruins = []
    for n, (a, b) in enumerate(pares):
        ka, kb = _K(a), _K(b)
        lento = KeyframeHandler.num_matches(ka, kb)
        rapido = num_matches_rapido(ka, kb)
        if lento != rapido:
            ruins.append((n, a.shape, b.shape, lento, rapido))
        elif verboso:
            print(f'   par {n}: {a.shape} x {b.shape}  ambos = {lento}')
    if ruins:
        for n, sa, sb, l, r in ruins:
            print(f'   ⛔ par {n}: {sa} x {sb}  original={l}  rapido={r}')
        raise SystemExit(f'⛔ {len(ruins)} de {len(pares)} pares DIVERGEM: '
                         'a vetorizacao nao e identica e NAO pode ser usada')
    print(f'  ✅ as duas implementacoes batem em {len(pares)} pares reais')
    return True


def instala():
    """Troca a implementação, depois de conferida pelo chamador."""
    KeyframeHandler.num_matches = staticmethod(num_matches_rapido)
