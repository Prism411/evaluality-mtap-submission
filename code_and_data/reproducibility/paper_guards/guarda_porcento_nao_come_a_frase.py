#!/usr/bin/env python3
r"""⛔ ALGUM `%` NAO ESCAPADO ESTA COMENDO O RESTO DA FRASE?

POR QUE EXISTE (22/09/2026). Ao integrar a prosa da revisao externa eu converti o Markdown
para .tex sem aplicar o escape de `%`. Duas frases entraram cruas:

  1. `...remain in the denominator. Thus the usual 50% orientation baseline applies...`
  2. `...and a positive lower bound of its 95% topic-block bootstrap confidence interval.`

⛔ **O `%` comeu o resto das duas linhas.** No PDF a pagina 10 terminava em «Thus the usual
50» e «a positive lower bound of its 95» — as duas definicoes que o leitor precisa para
interpretar o piso do acaso e a condicao de concordancia no dominio.

⚠️ **E NADA acusou**: o pdflatex compilou com 0 erros, as 44 guardas aprovaram e o
checklist deu 48/48. O texto some sem deixar rastro no log. Quem viu foi um revisor
humano lendo a pagina.

⭐ COMO SEPARA. Procura `%` em linha que NAO comeca com `%`, ignorando:
  - `\%`, que e o simbolo de porcentagem escapado, ou seja o uso correto;
  - `%` no fim da linha sem nada depois, que e o truque legitimo de colar palavras.
O alvo e `%` com conteudo imprimivel depois dele numa linha de texto.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
ARQS = ['main.tex', 'supplementary.tex'] + sorted(
    p.name for p in list(AQUI.glob('sec_*.tex')) + list(AQUI.glob('tab_*.tex'))
    + list(AQUI.glob('fig_*.tex')))


def suspeitas(texto=None, nome='<memoria>'):
    ruins = []
    fontes = [(nome, texto)] if texto is not None else \
        [(f, (AQUI / f).read_text(encoding='utf-8')) for f in ARQS if (AQUI / f).exists()]
    for f, t in fontes:
        for n, linha in enumerate(t.split('\n'), 1):
            if linha.lstrip().startswith('%'):
                continue                       # linha de comentario: assunto de outra guarda
            # ⭐ a assinatura do defeito e o `%` COLADO A UM DIGITO: e assim que um valor
            #    em porcentagem entra sem escape. Um `%` de comentario no fim de uma linha
            #    de texto e legitimo e nao perde nada, entao nao e alvo desta guarda.
            for m in re.finditer(r'(?<=\d)%', linha):
                i = m.start()
                if i and linha[i - 1] == '\\':
                    continue                   # `\%`: o simbolo, nao o comentario
                if not linha[i + 1:].strip():
                    continue                   # `%` colando palavras no fim da linha
                ruins.append((f, n, linha[max(0, i - 30):i], linha[i:i + 40]))
    return ruins


def _autoteste():
    bom = ('a taxa foi de 50\\% e o resto segue aqui\n'
           '%% um comentario sozinho\n'
           'palavra colada no fim%\n'
           'outra frase inteira\n')
    assert not suspeitas(bom), '⛔ falso positivo: %s' % suspeitas(bom)
    # ⭐ o mundo errado: os dois casos REAIS de 22/09, reintroduzidos
    for mau in ('Ties remain in the denominator. Thus the usual 50% orientation applies.\n',
                'a positive lower bound of its 95% topic-block bootstrap interval.\n'):
        assert suspeitas(mau), '⛔ NAO DISCRIMINA: o %% que come a frase passou'
    print('  autoteste ✅ (escapado e fim de linha passam; o que come a frase REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    r = suspeitas()
    for f, n, antes, depois in r:
        print('  ⛔ %s:%d  ...%s  ->  %s' % (f, n, antes, depois))
    print('  %d arquivo(s) varridos  |  %s' % (
        len(ARQS), '✅ APROVA' if not r else '⛔ %d `%%` comendo texto' % len(r)))
    sys.exit(0 if not r else 1)
