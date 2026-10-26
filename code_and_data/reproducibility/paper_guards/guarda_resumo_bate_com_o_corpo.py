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
    # ⛔ 21/09: O RESUMO FOI REESCRITO (parecer, A01), e esta lista descrevia o resumo
    # ANTERIOR. Pernas cujo fato saiu do resumo foram removidas, e as afirmacoes NOVAS
    # entraram: sem isso a guarda continuava verde sem cobrir nada do resumo atual, que e
    # o «controle que nao pode falhar». As que saem: «as dezesseis operacoes», «so uma e
    # indice autonomo», «e ela indexa colourfulness», «o BoVW inverte em 92 %», «nenhum
    # humano julgou» — nenhuma delas e afirmada pelo resumo de hoje.
    ('os 800 pares',                  r'800 pairs'),
    ('vinte segmentos em treze topicos',
     r'20 segments (?:come|com)[^.]{0,40}13 topics|20 broadcast segments|\\invRotulos\{\} topic'),
    ('a unidade mais conservadora',
     r'most conservative unit|over topics, the more conservative reading'),
    ('treze sob ruido branco',        r'thirteen do so under white noise|thirteen under white noise|resRuido\{\} do so under white noise'),
    ('o BoVW inverte em 92 %',        r'92\\%'),
    # ⚠️ o numero virou macro: aceitar o digito OU o nome da macro, sem tentar casar
    # a barra invertida, que so multiplica escape.
    ('797 dos 800',                   r'\b797\b|mecConcordam'),
    ('conta vezes peso medio',        r'count times a mean'),
    # ⚠️ 21/09: «No evaluated operation clears...» — o qualificador entrou por E51, que
    # pedia limitar a afirmacao aos membros TESTADOS. O fato e o mesmo.
    ('nenhuma passa os dois portoes',
     r'No (?:evaluated )?operation clears either damage gate|'
     r'No (?:evaluated )?operation clears either external (?:screening criterion|eligibility condition)'),
    ('nenhum composto passa',
     r'No combination evaluated here satisfies|none satisfies both|None of the nineteen (configurations )?satisfies both'),
    # ⚠️ os dois numeros viraram MACRO na reescrita de 21/09; a afirmacao e a mesma.
    ('tres de dez modelos passam',
     r'three of ten no-reference models|'
     # ⚠️ 22/09: a reescrita do parecer v3 usa a sigla «NR-IQA» na conclusao. E a mesma
     #    afirmacao; sem esta alternativa a regra reprovaria um corpo que continua dizendo.
     r'\\resElegiveis\{\} of \\invModelos\{\} (?:dedicated )?(?:no-reference|NR-IQA) models'),
    # ⚠️ o numero virou MACRO medida em 08/09 e o padrao literal parou de casar. A
    # afirmacao importa, nao a grafia: aceita o digito ou a macro que o produz.
    ('a troca muda 22 de 42',         r'(?:22|\\casCompleta\{\}) of (?:the )?42'),
    ('nenhum humano julgou a qualidade', r'No human (?:subjective )?quality (?:judgments|ratings)'),
    # ⚠️ a AFIRMACAO importa, nao a frase: em 08/09 ela foi condicionada ao requisito
    # medido e virou «better-supported replacement candidates». ⭐ 21/09, no
    # reenquadramento, ela virou de CLASSE: o remedio nao e um membro melhor da classe que
    # o campo ja usa, e sim a classe que ele quase nunca alcanca. A afirmacao e a mesma
    # (substituir, e nao normalizar), e a guarda reprovou a reescrita ate esta perna
    # entrar, que e o comportamento certo: obrigou a conferir se o fato sobreviveu.
    # ⛔ 21/09: a alternativa «the remedy is not a better member of the classes» foi
    # RETIRADA da lista, e nao apenas do corpo. D03 mandou tirar aquela frase por exceder
    # as variantes testadas; deixa-la aqui como padrao aceito deixaria a guarda verde
    # exatamente se a frase voltasse. Entrada morta reprova, e nao fica de reserva.
    ('a recomendacao de substituir',
     r'replace the operation rather than normalize|better-supported (?:replacement )?(?:candidates|alternatives)'),
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
    # ⛔ 04/10: a mutacao procurava a frase ANTIGA, literal e sensivel a caixa; com a
    # Secao 5 reescrita ela nao achava nada e o «mundo errado» saia identico ao certo.
    # Agora apaga a redacao atual e exige que a mutacao tenha mudado o texto.
    t = corpo()
    sujo = re.sub(r'[Nn]o human (?:subjective )?quality (?:judgments|ratings)',
                  'The bench shows', t)
    assert sujo != t, '⛔ nao consegui montar o mundo errado'
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
