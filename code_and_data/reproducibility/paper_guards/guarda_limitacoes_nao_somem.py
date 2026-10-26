#!/usr/bin/env python3
"""⛔ TODA LIMITACAO DECLARADA CONTINUA ESCRITA EM ALGUM LUGAR DO CORPO?

POR QUE EXISTE (08/09/2026). O [author] pediu para tirar a defesa espalhada e concentrar o
negativo numa secao so. Mover paragrafo e seguro; **cortar frase nao e**, e nenhuma outra
guarda ve o que deixou de estar escrito: o LaTeX compila igual, os numeros continuam
batendo, e a limitacao simplesmente some.

Na primeira rodada dessa reorganizacao **duas sumiram sem aviso**: que nenhum humano julgou
os segmentos, e o desenho do estudo que decidiria a questao. As duas foram restauradas na
§5.1.

⛔ Esta guarda NAO exige onde a frase esta, so que ela EXISTA. Concentrar na secao de
limitacoes e o objetivo; apagar nao e.

⚠️ 04/10/2026: a Secao 5 passou ao texto do [co-author], e seis padroes reprovaram com o
FATO ainda escrito (nao ha julgamento humano, alternativas redundantes, 19 topicos, degradacao
e nao preferencia, auxiliares descritivas, sinal legitimo removido). Os padroes foram ALARGADOS
para a redacao nova, sem tirar a antiga. Nenhuma limitacao desta lista saiu.

Autoteste de duas pernas: o corpo atual passa, e apagar uma limitacao REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# limitacoes cuja casa declarada e a configuracao do suplementar, e nao o corpo
NO_SUPLEMENTAR = {'a fusao oficial ficou fora'}
SUPLEMENTAR = ['supplementary.tex']

# (o que precisa continuar dito, padrao que reconhece)
LIMITACOES = [
    ('nenhum humano julgou a QUALIDADE',      r'No human quality judgments|no human preference|no human subjective quality ratings'),
    ('os membros do cluster sao alternativas',  r'redundant (?:segment )?alternatives'),
    ('os intervalos de saida cruzam zero',      r'cross(?:es)? zero|not confirm a\s*\n?population-level'),
    ('42 clusters aninhados em 19 topicos',     r'19 (?:news )?topics'),
    ('ARNIQA e TReS em eixos parciais',         r'ARNIQA and TReS'),
    ('MANIQA ausente',                          r'MANIQA'),
    ('a triagem admite mas nao ordena',         r'ranks nothing|without ordering|rather than a ranking'),
    ('DOVER nao isola modelagem temporal',      r'isolate temporal'),
    ('as referencias testam degradacao',        r'not preference between distinct recordings|rather than human preference between distinct video captures'),
    ('a fusao oficial ficou fora',              r'official standardized fusion|DOVER\+\+'),
    # ⚠️ o padrao trazia «auxiliary analyses», que era a palavra e nao a afirmacao:
    # ao uniformizar o vocabulario para «diagnostic control» a guarda reprovou sozinha.
    ('as auxiliares sao descritivas',
     r'(?:auxiliary (?:diagnostic )?analyses(?: presented)?|diagnostic controls) are descriptive'),
    ('condicionar por keypoint remove sinal',   r'legitimate (?:visual )?quality signal'),
    # ⚠️ o padrao trazia a grafia britanica e quebrou quando o artigo passou para o
    # americano. A AFIRMACAO importa, nao a grafia.
    ('o estudo humano que decidiria',           r'blind pairwise judge?ment'),
    ('qualidade decide dentro do grupo, nao o resumo',
     r'tie-breaker|basis for choosing a representative within a redundancy group'),
    # ⚠️ a AFIRMACAO importa, nao a frase: em 08/09 ela foi reescrita como «the verdict
    # travels with the benchmark» e a guarda reprovou um texto que continuava dizendo.
    ('o gabarito da triagem e um benchmark',
     # ⚠️ 21/09: a reescrita encurtou «between the KADID and the broadcast evaluation»
     #    para «between the two benchmarks». O FATO e o mesmo, e a frase seguinte
     #    («none meets it on both») continua sustentando-o.
     # ⚠️ 22/09 (parecer v2, V2-066): a frase precisou dizer que o que difere e o EIXO
     #    de sensibilidade, nao a elegibilidade inteira. O fato declarado e o mesmo, e
     #    «none meets it on both benchmarks» continua na mesma frase a sustenta-lo.
     r'conditional on the benchmark|verdict travels with the benchmark|'
     r'(?:[Ee]ligibility|The sensitivity axis alone already) differs between the '
     r'(KADID and the broadcast evaluation|two benchmarks)'),
    ('a regra de triagem nao foi pre-registrada', r'not\s+preregistered'),
    ('o ambiente nao e bit-identico',         r'bit-identical'),
]


def corpo(textos=None):
    # ⚠️ o espaco e normalizado ANTES de procurar: uma frase que quebra linha no meio
    # («blind pairwise\njudgement») nao pode reprovar por formatacao.
    t = textos if textos is not None else ' '.join(
        (AQUI / f).read_text(encoding='utf-8') for f in CORPO)
    return re.sub(r'\s+', ' ', t)


def _texto_do_suplementar():
    junto = ''
    for f in SUPLEMENTAR:
        q = AQUI / f
        if q.exists():
            junto += q.read_text(encoding='utf-8', errors='replace') + '\n'
    for q in sorted(AQUI.glob('tab_*.tex')):
        junto += q.read_text(encoding='utf-8', errors='replace') + '\n'
    return junto


def confere(textos=None):
    t = corpo(textos)
    sup = _texto_do_suplementar() if textos is None else ''
    faltam = []
    for nome, pat in LIMITACOES:
        onde = t + (sup if nome in NO_SUPLEMENTAR else '')
        if not re.search(pat, onde, re.I):
            faltam.append(nome)
    return not faltam, faltam, len(LIMITACOES)


def _autoteste():
    ok, faltam, n = confere()
    assert ok, '⛔ ja faltam: %s' % faltam
    # o mundo errado: uma limitacao apagada
    t = corpo()
    # ⚠️ sem `count`: a limitacao vive em mais de um lugar, e trocar so a primeira
    # deixava o «mundo errado» ainda correto.
    sujo = re.sub(r'[Nn]o human (?:subjective )?quality (?:judgments|ratings)', 'The audit shows', t)
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
