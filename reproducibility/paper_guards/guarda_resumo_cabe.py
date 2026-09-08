#!/usr/bin/env python3
"""⛔ O RESUMO CABE NO TETO DE PALAVRAS?

POR QUE EXISTE (08/09/2026). O resumo cresce por acrescimo: cada rodada de revisao poe uma
ressalva nova e ninguem reconta. Ele passou de 251 para 259 palavras sem que nada avisasse.
A revista da Springer pede resumo de ate 250 palavras.

⛔ E o teto e do TEXTO, nao do fonte: `\\textbf{}` e `$z$` nao sao palavras. A contagem
tira os comandos antes de contar.

Autoteste de duas pernas: um resumo curto passa e um resumo estourado REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
TETO = 250


def palavras(texto):
    """Conta palavras do TEXTO renderizado, nao do fonte.

    ⚠️ O cifrao NAO pode virar espaco: `$z$-score` e UMA palavra, e trocar `$` por espaco
    a partia em duas e inflava a contagem. Foi o autoteste que pegou isso.
    """
    s = re.sub(r'\\[a-zA-Z]+\{?', ' ', texto)   # comandos somem
    s = s.replace('$', '')                     # delimitador de matematica NAO separa
    s = re.sub(r'[{}\\~]', ' ', s)
    return len([w for w in s.split() if any(c.isalnum() for c in w)])


def resumo(fonte=None):
    t = fonte if fonte is not None else (AQUI / 'main.tex').read_text(encoding='utf-8')
    m = re.search(r'\\abstract\{(.*?)\n\}', t, re.S)
    return None if m is None else m.group(1)


def _autoteste():
    curto = '\\abstract{\n' + 'palavra ' * 10 + '\n}'
    longo = '\\abstract{\n' + 'palavra ' * (TETO + 5) + '\n}'
    assert palavras(resumo(curto)) <= TETO, '⛔ reprovou um resumo curto'
    assert palavras(resumo(longo)) > TETO, '⛔ NAO separa: um resumo estourado passou'
    # comando nao e palavra, e matematica nao parte palavra composta
    assert palavras(r'\textbf{}\emph{}') == 0, '⛔ conta comando como palavra'
    assert palavras(r'\textbf{um} $z$-score dois') == 3, '⛔ o cifrao esta partindo palavra'
    print('  autoteste ✅ (estourado REPROVA; comando nao conta; $z$-score conta 1)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    r = resumo()
    if r is None:
        print('  ⛔ nao achei \\abstract{...} em main.tex')
        sys.exit(2)
    n = palavras(r)
    print('  %d palavras, teto %d' % (n, TETO))
    print('  %s' % ('✅ APROVA' if n <= TETO else '⛔ REPROVA: %d acima' % (n - TETO)))
    sys.exit(0 if n <= TETO else 1)
