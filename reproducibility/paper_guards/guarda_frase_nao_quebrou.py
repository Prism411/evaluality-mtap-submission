#!/usr/bin/env python3
"""⛔ CORTAR UMA FRASE DEIXOU A VIZINHA QUEBRADA?

POR QUE EXISTE (08/09/2026). A reorganizacao tira frases de dentro de paragrafos, e a
pontuacao da frase ANTERIOR fica orfã. O LaTeX compila, os numeros continuam batendo,
nenhuma outra guarda reclama, e o artigo sai com «...without darkening and desaturation;
The 19 extractor substitutions...» — um ponto-e-virgula pendurado onde havia uma oracao.

Foi assim mesmo que aconteceu: removi «neither result is a human judgment.» e o `;` que a
introduzia ficou. So apareceu quando li o paragrafo.

⚠️ FALSO POSITIVO QUE PRECISA FICAR DE FORA: este artigo suprime o zero a esquerda, entao
«is .938» tem espaco antes do ponto DE PROPOSITO. A regra so vale quando a pontuacao nao
inicia um numero.

Autoteste de duas pernas: o corpo atual passa, e o defeito reintroduzido REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# ⚠️ `;` seguido de MAIUSCULA e quase sempre legitimo neste artigo: nome proprio, sigla
# de metodo, «; Bonferroni correction gives...». O que denuncia frase removida e o `;`
# seguido de um DETERMINANTE, que so aparece no comeco de uma oracao nova.
DETERMINANTE = r'The|This|These|Those|Its|Their|It|A|An|We|Our'

ARTEFATOS = [
    (re.compile(r';\s+(?:%s)\s' % DETERMINANTE), 'oracao removida apos ponto-e-virgula'),
    # espaco antes de pontuacao, exceto quando a pontuacao inicia um numero (.938)
    (re.compile(r'[a-zA-Z]\s+[.,;:](?![0-9])'), 'espaco antes de pontuacao'),
    (re.compile(r'\.\s*\.'), 'ponto duplo'),
    (re.compile(r'\b(\w+)\s+\1\b'), 'palavra repetida'),
    (re.compile(r'\(\s*\)|\[\s*\]'), 'delimitador vazio'),
    (re.compile(r',\s*(?:and|but|or)\s*[.;]'), 'conjuncao sem complemento'),
]


def plano(f):
    t = re.sub(r'(?m)^%.*$', '', (AQUI / f).read_text(encoding='utf-8'))
    return re.sub(r'\s+', ' ', t)


def confere(textos=None):
    achados = []
    fontes = textos if textos is not None else {f: plano(f) for f in CORPO}
    for f, t in fontes.items():
        for pat, nome in ARTEFATOS:
            for m in pat.finditer(t):
                achados.append((f, nome, t[max(0, m.start() - 46):m.end() + 46]))
    return not achados, achados


def _autoteste():
    ok, ach = confere()
    assert ok, '⛔ ja ha artefato: %s' % ach[:2]
    # perna 2: o defeito real de 08/09, reintroduzido
    sujo = {'x.tex': 'reaches 99.8 without darkening and desaturation; The 19 extractor '
                     'substitutions average 44.9 per cent.'}
    assert not confere(sujo)[0], '⛔ NAO separa: o ponto-e-virgula pendurado passou'
    # e o decimal do artigo NAO pode ser acusado
    limpo = {'x.tex': 'the coefficient of variation is .938 for the count and .098 for the '
                      'weight; Table~S4 lists both.'}
    assert confere(limpo)[0], '⛔ acusou o decimal sem zero a esquerda: %s' % confere(limpo)[1]
    print('  autoteste ✅ (pendurado REPROVA; «is .938» e «; Table» passam)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ach = confere()
    print('  %d arquivos varridos' % len(CORPO))
    if not ok:
        print('  ⛔ REPROVA: %d artefato(s) de corte' % len(ach))
        for f, nome, ctx in ach[:12]:
            print('    %-18s %-34s ...%s...' % (f, nome, ctx))
        sys.exit(1)
    print('  ✅ APROVA: nenhuma frase quebrada por corte')
