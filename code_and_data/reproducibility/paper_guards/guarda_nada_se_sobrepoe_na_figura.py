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
# ⚠️ 21/09: a secao nova do suplementar imprime `100(ȳ − l̄)/(h̄ − l̄)`, e a barra da
# ULTIMA letra dentro do parenteses encosta no proprio parenteses. Conferido
# renderizando a p.40: a formula sai correta e legivel. Mesma classe dos pares ja
# declarados — barra de `\overline{}` lida como palavra sobre o vizinho.
ISENTOS = {('¯', 'l'), ('l', '¯'), ('¯', 'd'), ('d', '¯'), ('¯', 'f'), ('f', '¯'),
           ('¯', ')'), (')', '¯'), ('¯', '):'), ('):', '¯')}


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


# palavras que ancoram as duas bandas da peca: a legenda mais baixa de cada
# painel, e a primeira palavra do rodape. Sao ancoras de LAYOUT, nao de redacao.
# ⚠️ 27/09: reancoradas no desenho novo. As anteriores («transformation»,
# «Meeting») eram do layout de quatro paineis e deixariam a funcao levantar.
RODAPE = ('Validate',)
LEGENDA_BAIXA = ('copy', 'selections')


def folga_ate_a_faixa(pdf):
    """Distancia entre a legenda mais baixa dos paineis e o topo do rodape.

    ⭐ Precisa passar de INNER_SEP, senao a legenda encosta na divisoria do rodape
    mesmo sem nenhuma palavra se sobrepor a outra.

    ⛔ 27/09: esta funcao estava INERTE. Ela procurava «ranking» e «Five evidence
    blocks», de um layout que o resumo grafico ja nao tinha, devolvia None, e quem
    a chamava tinha um `f is None or ...` que transformava o None em aprovacao.
    Controle que nao pode reprovar e o defeito, nao a protecao: agora ela LEVANTA
    se nao achar a estrutura, em vez de devolver None.
    """
    cx = caixas(pdf)
    fim = [x for x in cx if any(w in x[4] for w in LEGENDA_BAIXA)]
    faixa = [x for x in cx if x[4] in RODAPE]
    assert fim and faixa, (
        '⛔ a ancora do layout sumiu do resumo grafico (legenda=%d, rodape=%d): '
        'a folga deixaria de ser medida em silencio. Reancore em LEGENDA_BAIXA '
        'e RODAPE.' % (len(fim), len(faixa)))
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
    if f <= INNER_SEP:
        maus.append((PDFS[0], 'legenda de painel', 'rodape', 0.0, round(f, 1)))
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
    assert f > INNER_SEP, '⛔ a legenda ja encosta no rodape: folga %.1f pt' % f
    print('  autoteste ✅ (caixas empilhadas REPROVAM; vizinhas de linha nao; '
          'folga da legenda ate o rodape = %.1f pt)' % f)
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, maus, total = confere()
    print('  %d palavras medidas no graphical abstract' % total)
    for m in maus[:8]:
        print('    ⛔ %s: «%s» sobre «%s» (%.1f x %.1f pt)' % m)
    print('  %s' % ('✅ APROVA: nada se sobrepoe' if ok else '⛔ REPROVA: %d par(es)' % len(maus)))
    sys.exit(0 if ok else 1)
