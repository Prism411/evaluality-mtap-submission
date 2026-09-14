#!/usr/bin/env python3
"""A TABELA DAS DUAS RODADAS DA OPERACAO IMPLANTADA.

POR QUE EXISTE (08/09/2026). A objecao mais forte contra auditar o sistema de outra pessoa e
«voces implementaram errado». A resposta e uma segunda rodada, independente, no mesmo
desenho — e ela precisa aparecer TIPO A TIPO, porque a media esconde o unico lugar em que as
duas divergem.
"""
import os
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_reimplementacao.tex'
TIPOS = [('dark', 'Darken'), ('motion', 'Motion'), ('blur', 'Blur'), ('h264', 'H.264'),
         ('rescale', 'Rescale'), ('satur', 'Satur.'), ('noise', 'Noise'), ('jpeg', 'JPEG')]


# ⚠️ os nomes INTERNOS («noise», «satur», «jpeg») vazaram para a legenda na primeira
# versao. A legenda e prosa: usa o nome que o leitor ve na tabela.
LEGIVEL = {'dark': 'darkening', 'motion': 'motion blur', 'blur': 'Gaussian blur',
           'h264': 'H.264', 'rescale': 'rescaling', 'satur': 'desaturation',
           'noise': 'white noise', 'jpeg': 'JPEG'}


def cor(v):
    return r'\textcolor{accentred}{\textbf{%.0f}}' % v if v < 50 else '%.0f' % v


def main():
    d = json.loads((QB / 'a_reimplementacao_reproduz_a_falha.json').read_text(encoding='utf-8'))
    rep, rei = d['reportada'], d['reimplementacao']
    cab = ' & '.join(r'\hd{%s}' % r for _, r in TIPOS)
    l1 = ' & '.join(cor(rep['por_tipo'][k]) for k, _ in TIPOS)
    l2 = ' & '.join(cor(rei['por_tipo'][k]) for k, _ in TIPOS)
    div = d['⚠️_colapsam_so_na_reportada']
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{The deployed operation measured twice on the same %d pairs: the reported '
        'run and an independent reimplementation of the same published operation under the '
        'same protocol. \\textbf{The failure reproduces}: both collapse on %s, and both stay '
        'below the weakest published no-reference model at %.1f per cent. They differ on %s, '
        'where the reported run inverts and the reimplementation does not, which is the one '
        'place where implementation detail changes a verdict. Red marks a cell below the 50 '
        'per cent chance floor.}\n'
        % (d['n_pares'], ' and '.join(LEGIVEL[x] for x in d['colapsam_nas_duas']), d['pior_modelo_publicado'],
           ' and '.join(LEGIVEL[x] for x in div) if div else 'no type') +
        '\\label{tab:reimplementacao}\n'
        '\\scriptsize\n\\setlength{\\tabcolsep}{2.2pt}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{2.6cm}cccccccc c@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Run} & %s & \\hd{Mean} \\\\\n\\midrule\n' % cab +
        'Reported & %s & \\textbf{%.1f} \\\\\n' % (l1, rep['media']) +
        '\\rowcolor{rowlight}Independent reimplementation & %s & \\textbf{%.1f} \\\\\n'
        % (l2, rei['media']) +
        '\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  duas rodadas -> %s' % SAIDA.name)


if __name__ == '__main__':
    main()
