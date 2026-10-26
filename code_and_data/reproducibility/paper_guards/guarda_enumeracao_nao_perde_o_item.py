#!/usr/bin/env python3
r"""⛔ ALGUMA ENUMERACAO FICOU COM A CITACAO E SEM O NOME?

POR QUE EXISTE (22/09/2026, parecer v5). Ao integrar a prosa da revisao eu converti
«Nome et al.~\citep{x}» em «\citet{x}» com uma expressao regular, e depois desfiz a troca
onde o «nome» era na verdade um MODELO. ⛔ A volta apagou os nomes: a 2.2 ficou com

  «natural-scene-statistics models, ~\citep{mittal2012brisque,mittal2013niqe}»
  «DBCNN, HyperIQA, ~\citep{chen2024topiq,...}»
  «CLIP-IQA+~\citep{...}, ~\citep{zhang2023liqe} and ~\citep{agnolucci2024qualiclip}»

Tres enumeracoes viraram listas de citacoes sem itens. ⚠️ O LaTeX compila, a bibliografia
resolve, e o texto sai com virgulas seguidas de colchetes. Quem viu foi o revisor.

⭐ A ASSINATURA: uma citacao precedida IMEDIATAMENTE por virgula, dois-pontos ou «and»,
sem palavra nenhuma entre eles. Numa enumeracao sadia sempre ha o nome do item antes.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
ARQS = ['main.tex'] + sorted(p.name for p in AQUI.glob('sec_*.tex'))
# `,\citep` colado e a forma legitima de citar duas fontes seguidas; o alvo e o ESPACO
# entre o separador e a citacao, que so aparece quando o item some.
# ⚠️ so a forma PARENTETICA: `\citet` imprime o sobrenome, entao «and \citet{x} showed»
# e uma frase correta. Quem perde o item e o `\citep`, que nao imprime nome nenhum.
PAD = re.compile(r'(?:[,:;]|\band\b)\s+~?\\citep\{')


def suspeitas(texto=None, nome='<memoria>'):
    fontes = [(nome, texto)] if texto is not None else \
        [(f, (AQUI / f).read_text(encoding='utf-8')) for f in ARQS if (AQUI / f).exists()]
    ruins = []
    for f, t in fontes:
        t = re.sub(r'(?m)^%.*$', '', t)
        for m in PAD.finditer(t):
            ruins.append((f, t[:m.start()].count('\n') + 1, t[max(0, m.start() - 44):m.end() + 18]))
    return ruins


def _autoteste():
    bom = ('models such as BRISQUE and NIQE~\\citep{a,b} are used, and LIQE~\\citep{c} too.\n'
           'a phrase with a normal citation~\\citep{d}.\n')
    assert not suspeitas(bom), '⛔ falso positivo: %s' % suspeitas(bom)
    assert not suspeitas('and \\citet{jeong2016static} combined two terms.\n'), \
        '⛔ falso positivo: \\citet imprime o nome e e legitimo depois de «and»'
    for mau in ('the candidates include statistics models, ~\\citep{a,b}; and others.\n',
                'CLIP-IQA+~\\citep{x}, ~\\citep{y} and ~\\citep{z}.\n'):
        assert suspeitas(mau), '⛔ NAO DISCRIMINA: a enumeracao sem item passou'
    print('  autoteste ✅ (enumeracao com nomes passa; sem o item REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    r = suspeitas()
    for f, n, ctx in r:
        print('  ⛔ %s:%d  ...%s' % (f, n, re.sub(r'\s+', ' ', ctx)))
    print('  %d arquivo(s) varridos  |  %s' % (
        len(ARQS), '✅ APROVA' if not r else '⛔ %d citacao(oes) sem o item' % len(r)))
    sys.exit(0 if not r else 1)
