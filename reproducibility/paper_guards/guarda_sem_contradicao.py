#!/usr/bin/env python3
"""⛔ DUAS PARTES DO ARTIGO AFIRMAM COISAS INCOMPATIVEIS?

POR QUE EXISTE (08/09/2026). Quando baixei o Gygli e a P.910, atualizei a §3.1 para «all ten
are in the archive and were read» e **esqueci a §4.6, que continuou dizendo «The two we could
not read»**. Duas frases do mesmo artigo se contradizendo. Compilou, os numeros bateram, as
dezenove guardas aprovaram, e foi um revisor humano que viu.

⭐ Este e o erro que mais se repetiu na revisao: **eu atualizo um lugar e esqueco o outro**.
As guardas que existiam cobrem o caso de a afirmacao SUMIR; nenhuma cobria o caso de ela
sobreviver em duas versoes incompativeis.

⚠️ Detectar contradicao em geral e impossivel. O que da e declarar os pares que ESTE artigo
pode contradizer — cada par e uma afirmacao e a sua negacao — e exigir que no maximo um lado
apareca. A lista cresce quando um par novo aparecer.

Autoteste de duas pernas: o corpo atual passa, e plantar o lado oposto REPROVA.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
ARQS = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
        'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# (assunto, padrao do lado A, padrao do lado B) — os dois nao podem coexistir
PARES = [
    ('as fontes foram lidas ou nao',
     r'all ten are in the archive and were read|were read',
     r'we could not read|full text is not in the archive|whose full text is not'),
    ('spatial information tem ou nao veredito',
     r'spatial information[^.]{0,80}(?:carries no verdict|receives no screening verdict|'
     r'diagnostic control)',
     r'spatial information[^.]{0,60}(?:is eligible|clears both|passes the screening)'),
    ('a operacao implantada esta ou nao entre as dezesseis',
     r'is \\emph\{not\} one of the sixteen|which is not one of the fifteen|'
     r'not one of the (?:fifteen|sixteen)',
     r'the deployed (?:score|operation) is one of the (?:fifteen|sixteen)'),
    ('o mecanismo vale para uma ou para a classe',
     r'established for one operation|for one operation',
     r'establishes the mechanism for (?:all|every|the class)'),
    ('houve ou nao julgamento humano dos segmentos',
     r'[Nn]o human judged',
     r'human (?:raters|judges|participants) (?:rated|judged|assessed) these segments'),
]


def texto(fontes=None):
    if fontes is not None:
        return fontes
    t = ' '.join((AQUI / f).read_text(encoding='utf-8') for f in ARQS if (AQUI / f).exists())
    return re.sub(r'\s+', ' ', re.sub(r'(?m)^\s*%.*$', '', t))


def confere(fontes=None):
    t = texto(fontes)
    ruins = []
    for assunto, a, b in PARES:
        ma, mb = re.search(a, t, re.I), re.search(b, t, re.I)
        if ma and mb:
            ruins.append('%s:\n        A: ...%s...\n        B: ...%s...'
                         % (assunto,
                            t[max(0, ma.start() - 42):ma.end() + 42].strip(),
                            t[max(0, mb.start() - 42):mb.end() + 42].strip()))
    return not ruins, ruins


def _autoteste():
    ok, r = confere()
    assert ok, '⛔ ja ha contradicao: %s' % r[:1]
    # o mundo errado: o defeito real de 08/09, reintroduzido
    SUJO = texto() + ' The two we could not read are marked as such rather than counted.'
    assert not confere(SUJO)[0], '⛔ NAO separa: a contradicao reintroduzida passou'
    LIMPO = 'The bench measured every pair and no human judged these segments.'
    assert confere(LIMPO)[0], '⛔ reprovou um texto sem contradicao'

    # ⭐ e CADA regra tem de pegar o seu proprio mundo errado, senao e regra morta:
    # uma lista de pares que nunca dispara aprova por nao olhar.
    base = texto()
    PLANTAS = [
        ('fontes lidas', ' The two we could not read are marked as such.'),
        ('spatial information', ' Spatial information is eligible under the rule.'),
        ('a implantada', ' The deployed score is one of the sixteen audited here.'),
        ('o mecanismo', ' The factorization establishes the mechanism for the class.'),
        ('julgamento humano', ' Human raters judged these segments in a controlled study.'),
    ]
    for nome, frase in PLANTAS:
        assert not confere(base + frase)[0], \
            '⛔ a regra de %r nao pega o proprio defeito: e regra morta' % nome
    print('  autoteste ✅ (as %d regras pegam cada uma o seu defeito reintroduzido)'
          % len(PLANTAS))
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins = confere()
    print('  %d pares de afirmacoes incompativeis conferidos' % len(PARES))
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA: nenhum par aparece dos dois lados' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
