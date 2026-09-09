#!/usr/bin/env python3
"""⛔ ALGUMA FRASE ABRE COM UMA MACRO QUE RENDERIZA EM MINUSCULA?

POR QUE EXISTE (08/09/2026). As macros medidas emitem numeros por extenso em minuscula
(«five», «nine»), porque quase sempre aparecem no meio da frase. Quando uma cai no COMECO,
o PDF sai com «\\valSoResumo{} report agreement...» renderizado como «five report
agreement...», e o fonte parece perfeito: no `.tex` esta escrito `\\valSoResumo`, nao
`five`. Nenhuma leitura do fonte pega, e o compilador nao reclama.

Aconteceu duas vezes no mesmo dia, com macros diferentes, e as duas so apareceram lendo o
PDF renderizado.

Autoteste de duas pernas: uma frase que abre com maiuscula passa, e uma que abre com macro
minuscula REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
# ⛔ BURACO MEDIDO EM 09/09: o `main.tex` NAO estava na lista, e e onde mora o RESUMO.
# Uma macro minuscula abriu frase la e a guarda nao viu, porque nao abria o arquivo.
CORPO = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']


def macros_minusculas():
    """As macros medidas cujo valor comeca em minuscula."""
    mac = AQUI / 'regras_publicadas.tex'
    if not mac.exists():
        return {}
    out = {}
    for k, v in re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]*)\}',
                           mac.read_text(encoding='utf-8')):
        limpo = re.sub(r'\\[a-zA-Z]+|[${}]', '', v).strip()
        if limpo and limpo[0].islower():
            out[k] = limpo
    return out


def confere(fontes=None):
    minus = macros_minusculas()
    if not minus:
        return True, [], 0
    alvo = r'\\(' + '|'.join(sorted(minus, key=len, reverse=True)) + r')\{\}'
    # inicio de frase: apos ponto final, ou apos linha em branco
    padrao = re.compile(r'(?:(?<=\.)\s+|\n\n\s*)(?:\\textbf\{|\\emph\{)?' + alvo)
    fontes = fontes or {f: (AQUI / f).read_text(encoding='utf-8') for f in CORPO}
    ruins = []
    for nome, txt in fontes.items():
        t = re.sub(r'(?m)^%.*$', '', txt)
        for m in padrao.finditer(t):
            k = m.group(1)
            ruins.append('%s: frase abre com \\%s{}, que renderiza «%s»'
                         % (nome, k, minus[k]))
    return not ruins, ruins, len(minus)


def _autoteste():
    ok, r, n = confere()
    assert ok, '⛔ ja ha: %s' % r
    minus = macros_minusculas()
    assert minus, '⛔ nenhuma macro minuscula: aprovaria no vacuo'
    k = sorted(minus)[0]
    BOM = {'x.tex': 'The bench measured every pair. Of the fourteen, \\%s{} belong here.' % k}
    RUIM = {'x.tex': 'The bench measured every pair. \\%s{} belong to the inventory.' % k}
    assert confere(BOM)[0], '⛔ reprovou uma frase que abre com maiuscula'
    assert not confere(RUIM)[0], '⛔ NAO separa: frase abrindo com macro minuscula passou'
    print('  autoteste ✅ (frase abrindo com macro minuscula REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins, n = confere()
    print('  %d macros medidas renderizam em minuscula' % n)
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
