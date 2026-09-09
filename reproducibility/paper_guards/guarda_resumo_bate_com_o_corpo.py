#!/usr/bin/env python3
"""⛔ CADA AFIRMACAO DO RESUMO TEM RESPALDO NO CORPO?

POR QUE EXISTE (08/09/2026). O resumo e a parte mais lida e a que menos se reconfere: ele
foi reescrito por inteiro depois que o corpo ja estava pronto, e sobrevive a edicoes que
mexem no corpo sem toca-lo. Uma afirmacao que o corpo deixou de sustentar continua la.

⛔ Isto NAO confere o valor do numero contra a fonte medida — quem faz isso e a
`guarda_numeros_da_tabela`. Confere que a AFIRMACAO existe nas duas pontas.

Autoteste de duas pernas: o estado atual passa, e uma afirmacao sem respaldo REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# (o que o resumo afirma, padrao que reconhece a mesma afirmacao no corpo)
AFIRMACOES = [
    ('as dezesseis operacoes',        r'sixteen (?:visual )?operations|sixteen of them'),
    ('so uma e indice autonomo',      r'stand-alone index|autonomous index'),
    ('e ela indexa colourfulness',    r'indexes colourfulness'),
    ('os 800 pares',                  r'800 pairs'),
    ('treze sob ruido branco',        r'thirteen do so under white noise|thirteen under white noise'),
    ('o BoVW inverte em 92 %',        r'92\\%'),
    # ⚠️ o numero virou macro: aceitar o digito OU o nome da macro, sem tentar casar
    # a barra invertida, que so multiplica escape.
    ('797 dos 800',                   r'\b797\b|mecConcordam'),
    ('conta vezes peso medio',        r'count times a mean'),
    ('nenhuma passa os dois portoes', r'No operation clears either damage gate'),
    ('nenhum composto passa',         r'No combination evaluated here satisfies|none satisfies both'),
    ('tres de dez modelos passam',    r'three of ten no-reference models'),
    # ⚠️ o numero virou MACRO medida em 08/09 e o padrao literal parou de casar. A
    # afirmacao importa, nao a grafia: aceita o digito ou a macro que o produz.
    ('a troca muda 22 de 42',         r'(?:22|\\casCompleta\{\}) of (?:the )?42'),
    ('nenhum humano julgou',          r'No human judged'),
    # ⚠️ a AFIRMACAO importa, nao a frase: em 08/09 ela foi condicionada ao requisito
    # medido e virou «better-supported replacement candidates».
    ('a recomendacao de substituir',
     r'replace the operation rather than normalize|better-supported replacement candidates'),
]


def corpo():
    return ' '.join(re.sub(r'\s+', ' ', (AQUI / f).read_text(encoding='utf-8')) for f in CORPO)


def confere(texto=None):
    t = texto if texto is not None else corpo()
    faltam = [nome for nome, pat in AFIRMACOES if not re.search(pat, t, re.I)]
    return not faltam, faltam


def _autoteste():
    ok, faltam = confere()
    assert ok, '⛔ ja faltam: %s' % faltam
    # ⚠️ sem `count`: a afirmacao vive em mais de um lugar, e trocar so a primeira
    # deixava o «mundo errado» ainda correto, entao o autoteste falhava sozinho.
    sujo = re.sub(r'No human judged|no human judged', 'The bench shows', corpo())
    assert not confere(sujo)[0], '⛔ NAO separa: afirmacao sem respaldo passou'
    print('  autoteste ✅ (afirmacao sem respaldo no corpo REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, faltam = confere()
    print('  %d afirmacoes do resumo, todas com respaldo no corpo' % len(AFIRMACOES)
          if ok else '  %d sem respaldo' % len(faltam))
    for x in faltam:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
