#!/usr/bin/env python3
"""⛔ DUAS PALAVRAS OCUPANDO A MESMA AREA NO GRAPHICAL ABSTRACT?

POR QUE EXISTE (13/09/2026). Ao reequilibrar a peca eu aumentei o rotulo do cluster de duas
para quatro linhas, e ele desceu sobre a faixa de «Five evidence blocks». ⚠️ O LaTeX nao
reclama: TikZ posiciona o que mandarem, inclusive por cima de outra coisa. A compilacao
saiu com zero erro e o PDF com texto ilegivel, e quem achou foi um revisor.

⭐ A checagem nao olha a figura: mede as CAIXAS das palavras no PDF com `pdftotext -bbox` e
exige que nenhum par se cruze nos dois eixos.

⚠️ O cuidado que faz a guarda valer: palavras da MESMA linha encostam de lado o tempo todo.
Por isso a sobreposicao vertical tem de passar de metade da altura da menor das duas; senao
a guarda acusa espacamento normal e vira ruido.

Autoteste de duas pernas: o estado atual passa, e duas caixas montadas uma sobre a outra
REPROVAM.
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
PDFS = ['graphical_abstract.pdf']


def caixas(pdf):
    out = subprocess.run(['pdftotext', '-bbox', str(pdf), '-'],
                         capture_output=True, text=True).stdout
    return [(float(a), float(b), float(c), float(d), e) for a, b, c, d, e in
            re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                       r'yMax="([\d.]+)">([^<]*)</word>', out)]


def sobrepostos(cx, tol_x=1.5, fracao_y=0.5):
    maus = []
    for i in range(len(cx)):
        for j in range(i + 1, len(cx)):
            a, b = cx[i], cx[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > tol_x and oy > fracao_y * min(a[3] - a[1], b[3] - b[1]):
                maus.append((a[4], b[4], round(ox, 1), round(oy, 1)))
    return maus


def confere():
    total, maus = 0, []
    for nome in PDFS:
        p = AQUI / nome
        if not p.exists():
            continue
        cx = caixas(p)
        assert cx, '⛔ %s: nenhuma palavra lida, a guarda aprovaria no vacuo' % nome
        total += len(cx)
        maus += [(nome,) + m for m in sobrepostos(cx)]
    assert total, '⛔ nenhum PDF medido'
    return not maus, maus, total


def _autoteste():
    ok, maus, _ = confere()
    assert ok, '⛔ o estado atual deveria passar: %s' % maus[:2]
    # ⭐ o mundo errado: duas caixas na mesma area
    falso = [(10.0, 10.0, 40.0, 20.0, 'aqui'), (12.0, 11.0, 42.0, 21.0, 'ali')]
    assert sobrepostos(falso), '⛔ NAO pega duas caixas empilhadas'
    # e o mundo certo: palavras vizinhas na mesma linha nao podem acusar
    vizinhas = [(10.0, 10.0, 40.0, 20.0, 'uma'), (40.5, 10.0, 70.0, 20.0, 'outra')]
    assert not sobrepostos(vizinhas), '⛔ acusa espacamento normal entre palavras'
    print('  autoteste ✅ (caixas empilhadas REPROVAM; vizinhas de linha nao)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, maus, total = confere()
    print('  %d palavras medidas no graphical abstract' % total)
    for m in maus[:8]:
        print('    ⛔ %s: «%s» sobre «%s» (%.1f x %.1f pt)' % m)
    print('  %s' % ('✅ APROVA: nada se sobrepoe' if ok else '⛔ REPROVA: %d par(es)' % len(maus)))
    sys.exit(0 if ok else 1)
