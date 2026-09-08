#!/usr/bin/env python3
"""⛔ A MESMA AFIRMACAO ESTA DITA EM DUAS SECOES DIFERENTES?

POR QUE EXISTE (08/09/2026). O Jader pediu leitura coesa, sem reapresentar a justificativa
depois que o leitor ja entendeu. A repeticao nao entra de uma vez: ela se acumula porque
cada rodada de revisao acrescenta a explicacao no lugar onde o revisor sentiu falta, sem
tirar de onde ela ja estava.

Achou tres casos reais na primeira execucao: a analise «in closed form» dita na introducao,
na §2.3 e na §3; «relevancia, nao qualidade» em dois paragrafos seguidos da introducao; e a
lista das cinco partes do protocolo repetida em duas secoes.

⚠️ COMPARA IDEIA, NAO TEXTO. Duas frases com as mesmas palavras de conteudo dizem a mesma
coisa mesmo reescritas — foi assim que «conditional on the benchmark» e «the verdict travels
with the benchmark» apareceram como a mesma afirmacao. O limiar de Jaccard e 0,55, medido:
abaixo disso os pares eram frases legitimamente parecidas sobre numeros diferentes.

Autoteste de duas pernas: duas frases distintas passam, e a mesma frase em dois arquivos
REPROVA.
"""
import io
import itertools
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
ORD = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
       'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']
LIMIAR = 0.55
STOP = set('the a an of to in and or is are was were that this those these for on with as '
           'by it its at be not no than then so which what where when each one two both '
           'from into over under been have has had do does did can may might will would'.split())


def frases(texto):
    t = re.sub(r'(?m)^%.*$', '', texto)
    t = re.sub(r'\\(?:citep|citet|ref|label|input|newcommand)\{[^}]*\}', ' ', t)
    t = re.sub(r'\\[a-zA-Z]+\{?', ' ', t)
    t = re.sub(r'[{}$~\\]', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return [s.strip() for s in re.split(r'(?<=[.!?]) ', t) if len(s.split()) >= 9]


def sacola(s):
    return {w.lower().strip('.,;:()') for w in s.split()
            if w.lower() not in STOP and len(w) > 3}


def confere(fontes=None):
    if fontes is None:
        fontes = {f: (AQUI / f).read_text(encoding='utf-8') for f in ORD}
    todas = [(f, s) for f, txt in fontes.items() for s in frases(txt)]
    pares = []
    for (f1, s1), (f2, s2) in itertools.combinations(todas, 2):
        if f1 == f2:
            continue
        a, b = sacola(s1), sacola(s2)
        if not a or not b:
            continue
        j = len(a & b) / len(a | b)
        if j >= LIMIAR:
            pares.append((round(j, 2), f1, s1, f2, s2))
    return not pares, sorted(pares, reverse=True)


def _autoteste():
    ok, pares = confere()
    assert ok, '⛔ ja ha repeticao: %s' % (pares[:1],)
    LIMPO = {'a.tex': 'The deployed score inverts on ninety two per cent of the white noise '
                      'pairs measured here.',
             'b.tex': 'Three eligible models clear the operational screen on every unseen '
                      'database in the archive.'}
    assert confere(LIMPO)[0], '⛔ acusou duas frases que dizem coisas diferentes'
    MESMA = 'A mechanistic analysis available in closed form for the one published pipeline '\
            'component supplies the explanation here.'
    SUJO = {'a.tex': MESMA, 'b.tex': MESMA.replace('supplies', 'gives').replace('here', 'now')}
    assert not confere(SUJO)[0], '⛔ NAO separa: a mesma afirmacao reescrita passou'
    print('  autoteste ✅ (frases distintas passam; a mesma afirmacao reescrita REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, pares = confere()
    print('  %d secoes varridas, limiar de similaridade %.2f' % (len(ORD), LIMIAR))
    if ok:
        print('  ✅ APROVA: nenhuma afirmacao dita em duas secoes')
        sys.exit(0)
    print('  ⛔ REPROVA: %d par(es) dizendo o mesmo' % len(pares))
    for j, f1, s1, f2, s2 in pares[:6]:
        print('    %.2f  %-12s %s' % (j, f1.replace('sec_', '')[:10], s1[:78]))
        print('          %-12s %s' % (f2.replace('sec_', '')[:10], s2[:78]))
    sys.exit(1)
