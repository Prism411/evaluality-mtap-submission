#!/usr/bin/env python3
"""⛔ O RESUMO CABE NO TETO DE PALAVRAS?

POR QUE EXISTE (08/09/2026). O resumo cresce por acrescimo: cada rodada de revisao poe uma
ressalva nova e ninguem reconta. Ele passou de 251 para 259 palavras sem que nada avisasse.
A revista da Springer pede resumo de ate 250 palavras.

⛔ E o teto e do TEXTO, nao do fonte: `\\textbf{}` e `$z$` nao sao palavras. A contagem
tira os comandos antes de contar.

🔴 CORRIGIDO EM 13/09/2026, E A GUARDA ESTAVA ERRADA PARA MENOS. Ela apagava `\\macro{}`
junto com o comando, e cada macro medida IMPRIME UMA PALAVRA no PDF: `\\resElegiveis{}`
sai como «three». Com 14 macros no resumo, ela dizia 246 onde o PDF tem 259 — acima do
teto de 250 da revista. ⛔ E eu usei esse 246 para dizer a um revisor que ELE tinha errado.
⭐ Agora a contagem primaria e a do PDF RENDERIZADO, que e o que a revista le; o fonte
entra so como reserva, e com as macros expandidas.

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
    # ⭐ macro medida IMPRIME: expande antes de apagar comando, senao some uma palavra
    for k, v in macros_medidas().items():
        texto = texto.replace('\\%s{}' % k, ' %s ' % v).replace('\\%s ' % k, ' %s ' % v)
    s = re.sub(r'\\[a-zA-Z]+\{?', ' ', texto)   # comandos somem
    s = s.replace('$', '')                     # delimitador de matematica NAO separa
    s = re.sub(r'[{}\\~]', ' ', s)
    return len([w for w in s.split() if any(c.isalnum() for c in w)])


def do_pdf(pdf=None):
    """A contagem que vale: o texto que a revista de fato le.

    ⛔ Ler o fonte foi o defeito. Aqui o abstract sai do proprio PDF, entre a primeira
    frase dele e «Keywords».
    """
    import subprocess
    q = pdf or (AQUI / 'main.pdf')
    if not q.exists():
        return None
    out = subprocess.run(['pdftotext', '-f', '1', '-l', '2', str(q), '-'],
                         capture_output=True, text=True).stdout
    i = out.find('Video summarization systems select')
    j = out.find('Keywords', i) if i >= 0 else -1
    if i < 0 or j < 0:
        return None
    return len([w for w in out[i:j].split()
                if any(c.isalnum() for c in w) and w.strip() != '1'])


def macros_medidas():
    """rotulo -> texto impresso, lido do `regras_publicadas.tex`."""
    q = AQUI / 'regras_publicadas.tex'
    if not q.exists():
        return {}
    return dict(re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]*)\}',
                           q.read_text(encoding='utf-8')))


def resumo(fonte=None):
    t = fonte if fonte is not None else (AQUI / 'main.tex').read_text(encoding='utf-8')
    # ⛔ em 08/09 um COMENTARIO que citava «\abstract{}» fez o casamento comecar nele e o
    # resumo saltar de 250 para 365 palavras. Linha de comentario sai antes.
    t = re.sub(r'(?m)^\s*%.*$', '', t)
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
    n_fonte = palavras(r)
    n_pdf = do_pdf()
    n = n_pdf if n_pdf is not None else n_fonte
    print('  PDF renderizado: %s   fonte com macros expandidas: %d   teto %d'
          % (n_pdf if n_pdf is not None else '(sem PDF)', n_fonte, TETO))
    if n_pdf is not None and abs(n_pdf - n_fonte) > 3:
        print('  ⚠️ fonte e PDF divergem em %d: conferir se ha macro nova sem expansao'
              % abs(n_pdf - n_fonte))
    print('  %s' % ('✅ APROVA' if n <= TETO else '⛔ REPROVA: %d acima' % (n - TETO)))
    sys.exit(0 if n <= TETO else 1)
