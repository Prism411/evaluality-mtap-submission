#!/usr/bin/env python3
"""⛔ ALGUM COMANDO LATEX ESTA SAINDO IMPRESSO COMO TEXTO NO PDF?

POR QUE EXISTE (08/09/2026). A legenda da Tabela S17 saiu assim:

    «...alongside grey-scale intensity and a Canny detector in
     citetcakmak2025tripss
     , z(
     mathrmsharp) + 0.3 ...»

⭐ O gerador tinha `r'\\\\citet{...}'` numa RAW STRING: isso emite `\\\\citet` no `.tex`, e o
LaTeX le `\\\\` como QUEBRA DE LINHA e `citet{...}` como TEXTO. ⚠️ Compilou com ZERO erro,
zero warning, e passou por vinte e cinco guardas — porque todas conferem numero, frase e
ponteiro, e nenhuma abre o PDF para ver se sobrou comando impresso.

⭐ COMO SEPARA: le o TEXTO EXTRAIDO do PDF montado e procura nomes de comando soltos. Um
`citet` impresso nao existe em ingles; `emph`, `textbf`, `mathrm`, `newcommand` tambem nao.
E a leitura e do PDF, nao do fonte: e o unico lugar onde o defeito aparece.
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
PDFS = ['main.pdf', 'supplementary.pdf', 'graphical_abstract.pdf']
# nomes que NAO sao palavras de ingles e so aparecem se o comando vazou
COMANDOS = ['citet', 'citep', 'textbf', 'textit', 'emph', 'mathrm', 'newcommand',
            'renewcommand', 'begin{', 'end{', 'label{', 'caption{', 'rowcolor',
            'textcolor', 'multicolumn', 'hspace', 'vspace', 'footnotesize', 'scriptsize']


def texto(pdf):
    r = subprocess.run(['pdftotext', str(AQUI / pdf), '-'], capture_output=True, text=True)
    return r.stdout


def confere(textos=None):
    fontes = textos if textos is not None else {
        p: texto(p) for p in PDFS if (AQUI / p).exists()}
    ruins = []
    for p, t in fontes.items():
        for c in COMANDOS:
            for m in re.finditer(re.escape(c), t):
                # ⚠️ `emph` e `citet` podem aparecer dentro de outra palavra em ingles?
                # nenhum destes e subcadeia de palavra corrente; ainda assim so conta
                # quando NAO esta colado a uma letra antes, para nao pegar «recitet».
                if m.start() and t[m.start() - 1].isalpha():
                    continue
                ini = max(0, m.start() - 40)
                ruins.append('%s: ...%s...' % (p, t[ini:m.end() + 40].replace('\n', ' ')))
    return not ruins, ruins, len(fontes)


def autoteste():
    ok, ruins, _ = confere()
    if not ok:
        print('    ⛔ autoteste: os PDF atuais ja trazem comando impresso: %s' % ruins[:2])
        return False
    # ⛔ o defeito real de 08/09, replantado
    doente = {'x.pdf': 'a Canny detector in\ncitetcakmak2025tripss\n, z(\nmathrmsharp) + 0.3'}
    if confere(doente)[0]:
        print('    ⛔ autoteste: aprovou uma legenda com o comando vazado')
        return False
    # ⚠️ e a perna que impede acusacao em massa: prosa normal nao pode reprovar
    limpo = {'x.pdf': 'The deployed operation is correct on 65.1 per cent of 800 pairs, and '
                      'the citation of Hasler and Susstrunk (2003) is rendered normally.'}
    if not confere(limpo)[0]:
        print('    ⛔ autoteste: acusou prosa limpa')
        return False
    print('   autoteste ✅ (reprova o comando vazado; nao acusa prosa limpa)')
    return True


if __name__ == '__main__':
    if not autoteste():
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d PDF lidos em busca de comando LaTeX impresso como texto' % n)
    for x in ruins[:8]:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
