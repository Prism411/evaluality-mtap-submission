#!/usr/bin/env python3
"""⛔ O QUE A REVISTA EXIGE ESTA LA, E NADA FICOU PENDENTE?

POR QUE EXISTE (08/09/2026). O artigo estava com o texto pronto e **faltavam tres
declaracoes que a Springer exige**: Funding, Consent to participate e Consent for
publication. Nenhuma guarda olhava isso porque nenhuma delas e sobre o conteudo cientifico
— e e exatamente por isso que passam despercebidas ate a submissao ser devolvida.

⛔ E a segunda metade importa tanto quanto: um marcador `[A PREENCHER: ...]` compila, sai
bonito no PDF e vai junto para a revista. A guarda REPROVA enquanto algum sobreviver.

Autoteste de duas pernas: um texto completo passa, e a falta de uma declaracao ou a
presenca de um marcador REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent

EXIGIDAS = [
    'Competing interests', 'Funding', 'Data availability', 'Code availability',
    'Author contributions', 'Ethics approval', 'Consent to participate',
    'Consent for publication',
]
PENDENTE = re.compile(r'\[A PREENCHER|\bTODO\b|\bFIXME\b|\bXXX\b|\\todo\{|lorem ipsum', re.I)
# a marca vive tambem nos comentarios do fonte; so o que RENDERIZA conta
COMENTARIO = re.compile(r'(?m)^\s*%.*$')


def texto(fonte=None):
    t = fonte if fonte is not None else (AQUI / 'main.tex').read_text(encoding='utf-8')
    return COMENTARIO.sub('', t)


def confere(fonte=None):
    t = texto(fonte)
    # ⚠️ a Springer aceita declaracoes AGRUPADas num paragrafo so («Ethics approval, consent
    # to participate and consent for publication»). O que importa e o nome aparecer num
    # titulo de \paragraph, nao ter um \paragraph proprio.
    titulos = ' | '.join(re.findall(r'\\paragraph\{([^}]*)\}', t))
    faltam = [d for d in EXIGIDAS if d.lower() not in titulos.lower()]
    pend = [m.group(0) for m in PENDENTE.finditer(t)]
    outras = []
    if not re.search(r'\\keywords\{', t):
        outras.append('sem \\keywords')
    else:
        n = len([x for x in re.search(r'\\keywords\{([^}]*)\}', t, re.S).group(1).split(',')
                 if x.strip()])
        if not 3 <= n <= 8:
            outras.append('%d palavras-chave (a revista pede de 3 a 8)' % n)
    return (not faltam and not pend and not outras), faltam, pend, outras


def _autoteste():
    ok, f, p, o = confere()
    completo = ''.join(r'\paragraph{%s} texto.' % d for d in EXIGIDAS) + r'\keywords{a, b, c, d}'
    assert confere(completo)[0], '⛔ reprovou um texto completo: %s' % (confere(completo),)
    sem_funding = completo.replace(r'\paragraph{Funding}', r'\paragraph{Outra}')
    assert not confere(sem_funding)[0], '⛔ NAO separa: faltando Funding passou'
    agrupado = (r'\paragraph{Ethics approval, consent to participate and consent for '
                r'publication} texto.'
                + ''.join(r'\paragraph{%s} texto.' % d for d in EXIGIDAS
                          if d not in ('Ethics approval', 'Consent to participate',
                                       'Consent for publication'))
                + r'\keywords{a, b, c, d}')
    assert confere(agrupado)[0], '⛔ reprovou declaracoes agrupadas num paragrafo so'
    com_marca = completo + r' \textbf{[A PREENCHER: agencia]}'
    assert not confere(com_marca)[0], '⛔ NAO separa: marcador de pendencia passou'
    print('  autoteste ✅ (falta de declaracao e marcador pendente REPROVAM)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, faltam, pend, outras = confere()
    print('  %d declaracoes exigidas, %d presentes' % (len(EXIGIDAS), len(EXIGIDAS) - len(faltam)))
    for d in faltam:
        print('    ⛔ falta: \\paragraph{%s}' % d)
    for x in pend:
        print('    ⛔ pendencia no texto renderizado: %r' % x)
    for x in outras:
        print('    ⛔ %s' % x)
    if ok:
        print('  ✅ APROVA')
        sys.exit(0)
    # ⚠️ so pendencia de preenchimento nao e defeito do artigo: e decisao do autor.
    # Codigo 3 para o runner separar as duas coisas.
    if pend and not faltam and not outras:
        print('  ⏳ AGUARDA O AUTOR: a declaracao existe e o valor precisa ser preenchido')
        sys.exit(3)
    print('  ⛔ REPROVA')
    sys.exit(1)
