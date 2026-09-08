#!/usr/bin/env python3
"""⛔ AS DUAS TABELAS DIZEM, SOBRE CADA FONTE, O QUE A LEITURA DELA APUROU?

POR QUE EXISTE (08/09/2026). A clausula «tests the summary» / «never tests the rule» e uma
afirmacao sobre o artigo DE OUTRA PESSOA. Ela aparece em dois lugares (a banda da tabela do
corpo e a tabela documental do suplementar) e sai de um terceiro (o JSON da leitura). Tres
copias divergem sozinhas; esta guarda amarra as tres.

⛔ E ela cobre o erro que mais importa aqui: uma fonte SEM PDF nunca pode aparecer com
veredito. «Nao consta no acervo» e «nao validou» sao afirmacoes diferentes.

Autoteste de duas pernas: o estado atual passa, e um veredito plantado numa fonte nao lida
REPROVA.
"""
import io
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
QB = Path('/dados/Projetos/quality-benchmark')

# tipo no JSON -> trecho que a banda do corpo tem de carregar
BANDA = {
    'julgamento humano da propriedade': 'human ratings of the stated property',
    'so o resumo': 'summary-level agreement',
    'so o resumo, com ablacao de modulo': 'summary-level agreement, with ablation',
    'nem a regra nem os pesos': 'no isolated test of the rule',
}
SEM_PDF_BANDA = 'full text unavailable'


def confere(corpo=None, supl=None):
    d = json.load(open(QB / 'o_que_cada_fonte_valida.json'))
    corpo = corpo if corpo is not None else (AQUI / 'tab_sintese.tex').read_text(encoding='utf-8')
    supl = supl if supl is not None else (AQUI / 'tab_validacao.tex').read_text(encoding='utf-8')
    faltas = []

    for k, v in d['por_fonte'].items():
        esperado = BANDA[v['tipo']]
        banda = [l for l in corpo.split('\n') if ('citet{%s}' % k) in l and 'multicolumn' in l]
        if not banda:
            faltas.append('%s: sem banda no corpo' % k)
            continue
        if esperado not in banda[0]:
            faltas.append('%s: a banda nao diz %r' % (k, esperado))
        if SEM_PDF_BANDA in banda[0]:
            faltas.append('%s: foi LIDA, mas a banda diz que nao consta no acervo' % k)
        if v['verbatim'][:28] not in supl.replace('\\%', '%').replace('\\&', '&'):
            faltas.append('%s: o trecho literal nao esta no suplementar' % k)

    for k in d['sem_pdf_no_acervo']:
        banda = [l for l in corpo.split('\n') if ('citet{%s}' % k) in l and 'multicolumn' in l]
        if not banda:
            faltas.append('%s: sem banda no corpo' % k)
            continue
        if SEM_PDF_BANDA not in banda[0]:
            faltas.append('%s: sem PDF, mas a banda nao diz isso' % k)
        for t in BANDA.values():
            if t in banda[0]:
                faltas.append('⛔ %s: SEM PDF e a banda afirma %r' % (k, t))
    return not faltas, faltas, len(d['por_fonte']) + len(d['sem_pdf_no_acervo'])


def _autoteste():
    ok, f, n = confere()
    assert ok, '⛔ %s' % f
    corpo = (AQUI / 'tab_sintese.tex').read_text(encoding='utf-8')
    # o mundo errado: uma fonte NAO LIDA ganha veredito
    sujo = corpo.replace(SEM_PDF_BANDA, 'tests the summary', 1)
    assert sujo != corpo, '⛔ nao consegui montar o mundo errado'
    assert not confere(corpo=sujo)[0], '⛔ NAO separa: veredito numa fonte nao lida passou'
    print('  autoteste ✅ (com veredito plantado numa fonte nao lida, REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, faltas, n = confere()
    print('  %d fontes amarradas: JSON da leitura, banda do corpo e tabela do suplementar' % n)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    for x in faltas:
        print('    %s' % x)
    sys.exit(0 if ok else 1)
