#!/usr/bin/env python3
"""⛔ ALGUM COMENTARIO LaTeX ENGOLIU TEXTO QUE DEVIA SER IMPRESSO?

POR QUE EXISTE (21/09/2026). Ao reescrever o corpo eu cometi o MESMO erro duas vezes: pus
um comentario `%%` numa linha que ja tinha conteudo depois, e o `%` come o resto da LINHA.

  1. `...a frase fica generica. \\textbf{\\triTriadas{} of the`  -> comeu o `\\textbf{`, e o
     `}` da linha seguinte sobrou: «Too many }'s». ⭐ Esse o pdflatex ACUSA.
  2. `...variantes especificas. The supplement carries the exact relation between the two`
     -> comeu a oracao inteira, e a frase seguinte comecou em «inverse-document-frequency
     formulations, which differ by...». ⛔ **Esse NAO da erro nenhum**: compila limpo, sai
     no PDF como uma frase truncada, e so aparece LENDO.

⭐ O QUE ELA FAZ: procura linha que comece com texto (nao com `%`) e contenha ` %` ou `%%`
seguido de qualquer coisa. Em LaTeX, `%` no meio de uma linha de texto e quase sempre
comentario de fim de linha, que e legitimo para colar palavras sem espaco — mas ai ele vem
NO FIM, sem nada depois. Se ha conteudo depois do `%`, ou e comentario mal colocado (o
defeito) ou e um `%` de sintaxe.

⚠️ `\\%` escapado NAO conta: e o simbolo de porcentagem, nao comentario.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
ARQS = ['main.tex', 'supplementary.tex'] + sorted(p.name for p in AQUI.glob('sec_*.tex'))


def suspeitas(texto=None, nome='<memoria>'):
    """⛔ 22/09: A GUARDA OLHAVA O LADO ERRADO, e reprovava comentario legitimo.

    O defeito real de 21/09 foi uma linha que COMECA com `%%` e carrega, no fim, texto que
    devia ser impresso — o `%` come o resto da linha e aquele texto some. Texto seguido de
    comentario no fim da linha e o caso NORMAL e nao perde nada.

    ⭐ O alvo certo e, portanto: linha de comentario que contem, depois do texto do
    comentario, uma construcao que so faz sentido impressa.
    """
    ruins = []
    fontes = [(nome, texto)] if texto is not None else \
        [(f, (AQUI / f).read_text(encoding='utf-8')) for f in ARQS if (AQUI / f).exists()]
    for f, t in fontes:
        for n, linha in enumerate(t.split('\n'), 1):
            if not linha.lstrip().startswith('%'):
                continue                      # linha de texto: comentario no fim e ok
            corpo = linha.lstrip().lstrip('%')
            # ⭐ o sinal: um comando de TEXTO ou uma macro medida dentro do comentario,
            #    o que indica que uma linha do artigo foi colada ao fim do comentario.
            # so comandos de TEXTO: 'begin' e 'item' sairam porque um comentario
            # que EXPLICA a estrutura cita \begin{document} legitimamente.
            m = re.search(r'\\(textbf|emph|textit|citep|citet)\{', corpo)
            if m and not re.search(r'[«»"\'`]', corpo[max(0, m.start() - 40):m.start()]):
                ruins.append((f, n, corpo[:38], corpo[m.start():m.start() + 46]))
    return ruins


def _autoteste():
    bom = ('uma frase inteira aqui\n%% um comentario sozinho\noutra frase\n'
           'texto com 50\\% e fim\nfim de linha%\n'
           'a frase acaba aqui. %% e o comentario vem depois, com \xe2\x9b\x94 marcador\n')
    assert not suspeitas(bom), '⛔ falso positivo: %s' % suspeitas(bom)
    # ⭐ o mundo errado: o caso REAL de 21/09, uma linha de comentario que carrega no fim
    #    uma linha do artigo. Sem esta perna a guarda nao mede nada.
    mau1 = '%% a frase fica generica. \\textbf{\\triTriadas{} of the\n'
    mau2 = '%% variantes especificas. \\emph{The supplement} carries the exact relation\n'
    for m in (mau1, mau2):
        assert suspeitas(m), '⛔ NAO DISCRIMINA: o comentario que engole texto passou'
    print('  autoteste ✅ (comentario no fim de linha passa; comentario que engole REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    r = suspeitas()
    for f, n, a, d in r:
        print('  ⛔ %s:%d  ...%s  %%->  %s' % (f, n, a, d))
    print('  %d arquivo(s) varridos  |  %s'
          % (len(ARQS), '✅ APROVA' if not r else '⛔ %d linha(s) com texto apos comentario' % len(r)))
    sys.exit(0 if not r else 1)
