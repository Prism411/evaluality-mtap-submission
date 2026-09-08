#!/usr/bin/env python3
"""⛔ «N DE M, A EXCECAO SENDO X» — AS EXCECOES NOMEADAS BATEM COM M MENOS N?

POR QUE EXISTE (08/09/2026). O corpo dizia **«14 of the sixteen operations carry such an
excerpt, the exception being spatial information»**. Catorze de dezesseis implica DUAS
excecoes; a frase nomeia UMA. O numero vinha de uma macro medida, entao nenhuma guarda de
numero reclamou: o valor 14 existe na fonte, so que contando outra coisa (as nao-autonomas
com fonte, e nao os trechos conferidos, que sao 15).

⭐ Uma contagem pode estar CERTA em relacao a fonte e ERRADA em relacao a frase que a
carrega. Esta guarda confere a aritmetica interna do enunciado.

Autoteste de duas pernas: «fifteen of the sixteen ... the exception being» passa, e
«fourteen of the sixteen ... the exception being» REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

PALAVRA = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
           'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
           'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'nineteen': 19, 'twenty': 20}

# «N of the M ... the exception being X» / «... the exceptions being X and Y»
PADRAO = re.compile(
    r'\b(?P<n>\d+|' + '|'.join(PALAVRA) + r')\s+of\s+the\s+'
    r'(?P<m>\d+|' + '|'.join(PALAVRA) + r')\b'
    r'(?P<meio>[^.]{0,180}?)'
    r'the\s+(?P<plural>exceptions?)\s+(?:being|is|are)\s+(?P<lista>[^.;]{0,120})',
    re.I)


def num(s):
    s = s.lower()
    return int(s) if s.isdigit() else PALAVRA.get(s)


def texto(fontes=None):
    if fontes is not None:
        return fontes
    t = ' '.join((AQUI / f).read_text(encoding='utf-8') for f in CORPO)
    return re.sub(r'\s+', ' ', t)


def confere(fontes=None):
    t = texto(fontes)
    # as macros ja resolvidas: o teste roda sobre o .tex, entao troca as conhecidas
    mac = (AQUI / 'regras_publicadas.tex')
    if mac.exists():
        for k, v in re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]*)\}',
                               mac.read_text(encoding='utf-8')):
            t = t.replace('\\%s{}' % k, v)
    ruins = []
    for m in PADRAO.finditer(t):
        n, mm = num(m.group('n')), num(m.group('m'))
        if n is None or mm is None or mm <= n:
            continue
        lista = m.group('lista')
        # ⚠️ a virgula que abre uma APOSICAO nao separa outra excecao: em «spatial
        # information, classified from the purpose ...» ha UM item, nao dois. Corta no
        # participio ou pronome relativo que inicia a aposicao.
        lista = re.split(r',\s*(?:which|classified|measured|reported|taken|derived|'
                         r'defined|read|used|computed|whose|since|because)\b',
                         lista, maxsplit=1)[0]
        nomeadas = len([x for x in re.split(r',| and ', lista) if x.strip()])
        if nomeadas != mm - n:
            ruins.append('«%s of the %s ... %s %s»: a frase implica %d excecao(oes) e '
                         'nomeia %d' % (m.group('n'), m.group('m'), m.group('plural'),
                                        lista.strip()[:44], mm - n, nomeadas))
    return not ruins, ruins


def _autoteste():
    ok, r = confere()
    assert ok, '⛔ ja ha desacordo: %s' % r
    BOM = 'fifteen of the sixteen operations carry such an excerpt, the exception being '\
          'spatial information, classified from the purpose the recommendation states.'
    RUIM = BOM.replace('fifteen', 'fourteen')
    assert confere(BOM)[0], '⛔ reprovou uma contagem coerente'
    assert not confere(RUIM)[0], '⛔ NAO separa: «fourteen of the sixteen» com uma excecao passou'
    print('  autoteste ✅ (14 de 16 com UMA excecao nomeada REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins = confere()
    print('  enunciados «N de M, excecao X» conferidos')
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
