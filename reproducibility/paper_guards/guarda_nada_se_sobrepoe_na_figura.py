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
PDFS = ['graphical_abstract.pdf', 'supplementary.pdf', 'main.pdf']
# a barra de `\overline{...}` e lida como palavra sobre a letra: e formula, nao colisao
ISENTOS = {('¯', 'l'), ('l', '¯'), ('¯', 'd'), ('d', '¯'), ('¯', 'f'), ('f', '¯')}


def por_pagina(pdf):
    """As caixas das palavras, uma lista POR PAGINA.

    ⛔ Ler o documento inteiro numa lista so compara palavra de paginas diferentes: com o
    suplementar de 36 paginas isso acusou «Electronic» da capa contra «bebe» de outra.
    """
    out = subprocess.run(['pdftotext', '-bbox', str(pdf), '-'],
                         capture_output=True, text=True).stdout
    pags = re.findall(r'<page width="[\d.]+" height="[\d.]+">(.*?)</page>', out, re.S)
    return [[(float(a), float(b), float(c), float(d), e) for a, b, c, d, e in
             re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                        r'yMax="([\d.]+)">([^<]*)</word>', pg)] for pg in pags]


def caixas(pdf):
    """Todas as palavras, achatadas. So para quem nao precisa da divisao por pagina."""
    return [w for pg in por_pagina(pdf) for w in pg]


def sobrepostos(cx, tol_x=1.5, fracao_y=0.5):
    maus = []
    for i in range(len(cx)):
        for j in range(i + 1, len(cx)):
            a, b = cx[i], cx[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > tol_x and oy > fracao_y * min(a[3] - a[1], b[3] - b[1]):
                if (a[4], b[4]) in ISENTOS:
                    continue
                maus.append((a[4], b[4], round(ox, 1), round(oy, 1)))
    return maus


# a moldura desenhada em volta do texto do quadro de conclusoes, em pontos
INNER_SEP = 7.0


def folga_ate_a_faixa(pdf):
    """Distancia entre o fim do texto do quadro de conclusoes e o topo da faixa inferior.

    ⭐ Precisa passar de INNER_SEP, senao a CAIXA cruza a divisoria mesmo com as palavras
    separadas. Devolve None quando a peca nao tem essa estrutura.
    """
    cx = caixas(pdf)
    fim = [x for x in cx if 'ranking' in x[4]]
    faixa = [x for x in cx if x[4] in ('Five', 'evidence', 'blocks')]
    if not fim or not faixa:
        return None
    return min(x[1] for x in faixa) - max(x[3] for x in fim)


def confere():
    total, maus = 0, []
    for nome in PDFS:
        p = AQUI / nome
        if not p.exists():
            continue
        pgs = por_pagina(p)
        assert any(pgs), '⛔ %s: nenhuma palavra lida, a guarda aprovaria no vacuo' % nome
        for n_pg, cx in enumerate(pgs, 1):
            total += len(cx)
            maus += [('%s p%d' % (nome, n_pg),) + m for m in sobrepostos(cx)]
    assert total, '⛔ nenhum PDF medido'
    # ⭐ e a folga da CAIXA, que nao aparece na colisao entre palavras
    f = folga_ate_a_faixa(AQUI / PDFS[0])
    if f is not None and f <= INNER_SEP:
        maus.append((PDFS[0], 'quadro de conclusoes', 'faixa inferior', 0.0, round(f, 1)))
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
    f = folga_ate_a_faixa(AQUI / PDFS[0])
    assert f is None or f > INNER_SEP, '⛔ a caixa ja cruza a faixa: folga %.1f pt' % f
    print('  autoteste ✅ (caixas empilhadas REPROVAM; vizinhas de linha nao; '
          'folga da caixa ate a faixa = %.1f pt)' % (f if f is not None else -1))
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, maus, total = confere()
    print('  %d palavras medidas no graphical abstract' % total)
    for m in maus[:8]:
        print('    ⛔ %s: «%s» sobre «%s» (%.1f x %.1f pt)' % m)
    print('  %s' % ('✅ APROVA: nada se sobrepoe' if ok else '⛔ REPROVA: %d par(es)' % len(maus)))
    sys.exit(0 if ok else 1)
