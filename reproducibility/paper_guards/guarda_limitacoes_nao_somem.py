#!/usr/bin/env python3
"""⛔ TODA LIMITACAO DECLARADA CONTINUA ESCRITA EM ALGUM LUGAR DO CORPO?

POR QUE EXISTE (08/09/2026). O Jader pediu para tirar a defesa espalhada e concentrar o
negativo numa secao so. Mover paragrafo e seguro; **cortar frase nao e**, e nenhuma outra
guarda ve o que deixou de estar escrito: o LaTeX compila igual, os numeros continuam
batendo, e a limitacao simplesmente some.

Na primeira rodada dessa reorganizacao **duas sumiram sem aviso**: que nenhum humano julgou
os segmentos, e o desenho do estudo que decidiria a questao. As duas foram restauradas na
§5.1.

⛔ Esta guarda NAO exige onde a frase esta, so que ela EXISTA. Concentrar na secao de
limitacoes e o objetivo; apagar nao e.

Autoteste de duas pernas: o corpo atual passa, e apagar uma limitacao REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# (o que precisa continuar dito, padrao que reconhece)
LIMITACOES = [
    ('nenhum humano julgou os segmentos',      r'No human judged|no human preference|human judged these'),
    ('os membros do cluster sao alternativas',  r'redundant alternatives'),
    ('os intervalos de saida cruzam zero',      r'cross(?:es)? zero|not confirm a\s*\n?population-level'),
    ('42 clusters aninhados em 19 topicos',     r'19 topics'),
    ('ARNIQA e TReS em eixos parciais',         r'ARNIQA and TReS'),
    ('MANIQA ausente',                          r'MANIQA'),
    ('a triagem admite mas nao ordena',         r'ranks nothing|without ordering|rather than a ranking'),
    ('DOVER nao isola modelagem temporal',      r'isolate temporal'),
    ('as referencias testam degradacao',        r'not preference between distinct recordings'),
    ('a fusao oficial ficou fora',              r'official standardized fusion|DOVER\+\+'),
    ('as auxiliares sao descritivas',           r'auxiliary analyses are descriptive'),
    ('condicionar por keypoint remove sinal',   r'legitimate quality signal'),
    ('o estudo humano que decidiria',           r'blind pairwise judgement'),
    ('qualidade e criterio de desempate',       r'tie-breaker'),
    # ⚠️ a AFIRMACAO importa, nao a frase: em 08/09 ela foi reescrita como «the verdict
    # travels with the benchmark» e a guarda reprovou um texto que continuava dizendo.
    ('o gabarito da triagem e um benchmark',
     r'conditional on the benchmark|verdict travels with the benchmark'),
    ('a regra de triagem nao foi pre-registrada', r'not\s+preregistered'),
    ('o ambiente nao e bit-identico',         r'bit-identical'),
]


def corpo(textos=None):
    # ⚠️ o espaco e normalizado ANTES de procurar: uma frase que quebra linha no meio
    # («blind pairwise\njudgement») nao pode reprovar por formatacao.
    t = textos if textos is not None else ' '.join(
        (AQUI / f).read_text(encoding='utf-8') for f in CORPO)
    return re.sub(r'\s+', ' ', t)


def confere(textos=None):
    t = corpo(textos)
    faltam = [nome for nome, pat in LIMITACOES if not re.search(pat, t, re.I)]
    return not faltam, faltam, len(LIMITACOES)


def _autoteste():
    ok, faltam, n = confere()
    assert ok, '⛔ ja faltam: %s' % faltam
    # o mundo errado: uma limitacao apagada
    t = corpo()
    # ⚠️ sem `count`: a limitacao vive em mais de um lugar, e trocar so a primeira
    # deixava o «mundo errado» ainda correto.
    sujo = re.sub(r'[Nn]o human judged', 'The audit shows', t)
    assert sujo != t, '⛔ nao consegui montar o mundo errado'
    assert not confere(sujo)[0], '⛔ NAO separa: a limitacao apagada passou'
    print('  autoteste ✅ (apagando uma limitacao, a guarda REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, faltam, n = confere()
    print('  %d limitacoes declaradas, todas ainda escritas no corpo' % n
          if ok else '  %d de %d limitacoes SUMIRAM' % (len(faltam), n))
    for x in faltam:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
