#!/usr/bin/env python3
"""Figura: o que cada operacao da literatura faz com o resumo implantado.

⛔ SO o lado da sumarizacao. O lado NR-IQA do `jusante_lado_a_lado.json` NAO entra: o campo
`agree` do `kappa42_full.json` e concordancia com o **Q-Align**, nao com o SIFT implantado
(sec_results: "LIQE agrees with Q-Align on 32 of 42"), e alem disso o artigo amostra dez
quadros uniformes enquanto esta passada amostra a 1 fps. Duas bases e duas amostragens: nao
se lê de um lado para o outro. Aqui tudo vem de UMA passada, contra UMA base."""
import os
import json
import statistics as st
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'fig_jusante.tex'
NOME = {'sobel_cv': 'Sobel variation coeff.', 'contraste_variancia': 'Grey-level dispersion',
        'laplacian_var': 'Laplacian variance', 'huang_exposicao': 'Exposure',
        'brilho': 'Brightness', 'ke_brightness': 'Brightness (Ke)',
        'ke_contraste': 'Contrast (Ke)', 'hasler_colorfulness': 'Colourfulness (Hasler)',
        'ke_colorfulness': 'Colourfulness (Ke)', 'srinivas_quality': 'Composite of five',
        # ⚠️ «Hue count» e «Hue» em linhas vizinhas pareciam a mesma operacao duas vezes.
        # A figura ja usa o padrao «(Ke)»/«(Hasler)» nas outras duas duplicatas.
        'huang_saturacao': 'Saturation (Huang)', 'huang_matiz': 'Hue (Huang)',
        'ke_edge_distribution': 'Edge distribution (Ke)', 'ke_hue_count': 'Hue count (Ke)'}


def main():
    d = json.load(open(QB / 'jusante_lado_a_lado.json'))
    # ⛔ as 14 do jusante NAO sao as 16 auditadas: 5 delas nunca passaram pela triagem
    aud = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    L0 = sorted([x for x in d['linhas'] if 'sumarizacao' in x['familia']],
                key=lambda z: -z['pct'])
    piso, n = d['piso_do_acaso_pct'], d['n_clusters']
    assert len(L0) == 14, len(L0)
    W, bh, gap = 5.3, 0.222, 0.044
    COLNUM = W + 0.32                       # ⭐ os numeros saem da area do grafico: dentro
    base = -(len(L0)) * (bh + gap) - 0.10   # dela colidiam com a grade e com as verticais
    L = [r'\begin{figure}[!t]', r'\centering',
         r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]']
    for x in (0, 25, 50, 75, 100):
        px = x / 100 * W
        L += [f'\\draw[rulegray!30,line width=.3pt] ({px:.2f},0.16) -- ({px:.2f},{base:.2f});',
              f'\\node[font=\\scriptsize,text=black!45] at ({px:.2f},0.36) {{{x}}};']
    L.append(f'\\draw[accentred!85,line width=.9pt,dash pattern=on 2pt off 1.5pt] '
             f'({piso/100*W:.2f},0.16) -- ({piso/100*W:.2f},{base:.2f});')
    for i, x in enumerate(L0):
        y = -(i + 1) * (bh + gap) + gap
        ab = x['pct'] < piso
        L += [f'\\node[anchor=east,font=\\scriptsize] at (-0.14,{y+bh/2:.2f}) '
              f'{{{NOME[x["nome"]]}}};',
              f'\\fill[{"accentred!70" if ab else "catbovw!45"}] (0,{y:.2f}) rectangle '
              f'({x["pct"]/100*W:.2f},{y+bh:.2f});',
              f'\\node[anchor=west,font=\\scriptsize,text=black!'
              f'{"75" if ab else "55"}] at ({COLNUM:.2f},{y+bh/2:.2f}) '
              f'{{{x["concorda"]}/{x["n"]} \\ ({x["pct"]:.1f}\\%)}};']
    med = st.median([x['pct'] for x in L0])
    ab = [x for x in L0 if x['pct'] < piso]
    NUM = {14: 'fourteen', 9: 'nine', 5: 'five', 4: 'four', 3: 'three', 2: 'two', 1: 'one'}
    nomes = [x['nome'] for x in L0]
    naud = sum(1 for k in nomes if k in aud)
    eleg = sum(1 for k in nomes if k in aud and aud[k].get('elegivel'))
    assert eleg == 0, f'⛔ {eleg} das auditadas sao elegiveis: a frase da prosa cai'
    L += [f'\\fill[black!55] ({med/100*W-0.07:.2f},0.60) -- ({med/100*W+0.07:.2f},0.60) -- '
          f'({med/100*W:.2f},0.46) -- cycle;',
          f'\\node[anchor=south,font=\\scriptsize,text=black!55] at '
          f'({med/100*W:.2f},0.62) {{median {med:.1f}\\%}};',
          f'\\node[anchor=north,font=\\scriptsize,text=accentred!80!black] at '
          f'({piso/100*W:.2f},{base-0.06:.2f}) {{chance {piso:.0f}\\%}};',
          r'\end{tikzpicture}',
          r'\caption{What each operation does to the deployed summary. Every pipeline stage '
          r'is held fixed and only the visual-selection operation is replaced; the bar is the '
          rf'percentage of the {n} redundancy-cluster representatives that survive the swap. '
          rf'\textbf{{The median operation keeps {med:.1f} per cent of the decisions against '
          rf'a chance floor of {piso:.0f}}}, and the {NUM[len(ab)]} in red keep fewer than '
          r'chance. '
          r'Swapping one published operation for another therefore rewrites between '
          rf'{100-max(x["pct"] for x in L0):.0f} and {100-min(x["pct"] for x in L0):.0f} per '
          r'cent of what the stage outputs. Both the frames and the clusters are shared '
          r'across all fourteen operations and the deployed one, so nothing here comes from '
          r'a difference in sampling.}',
          r'\label{fig:jusante}', r'\end{figure}']
    # ⚠️ «hue count, hue» lado a lado na prosa parece a mesma operacao duas vezes.
    # Sao duas: a contagem de matizes do Ke e o termo de matiz do Huang.
    nom = {'ke_hue_count': "Ke's hue count", 'huang_matiz': "Huang's hue",
           'ke_edge_distribution': 'edge distribution', 'huang_saturacao': 'saturation'}
    ext = ', '.join(nom[x['nome']] for x in sorted(ab, key=lambda z: z['pct']))
    L = ([f'\\newcommand{{\\jusAbaixo}}{{{NUM[len(ab)]}}}',
          f'\\newcommand{{\\jusAbaixoNomes}}{{{ext}}}',
          f'\\newcommand{{\\jusMediana}}{{{med:.1f}}}',
          f'\\newcommand{{\\jusPiso}}{{{piso:.1f}}}',
          f'\\newcommand{{\\jusMin}}{{{min(x["pct"] for x in L0):.1f}}}',
          f'\\newcommand{{\\jusMax}}{{{max(x["pct"] for x in L0):.1f}}}',
          f'\\newcommand{{\\jusReescreveMin}}{{{100-max(x["pct"] for x in L0):.0f}}}',
          f'\\newcommand{{\\jusReescreveMax}}{{{100-min(x["pct"] for x in L0):.0f}}}',
          f'\\newcommand{{\\jusAuditadas}}{{{NUM[naud]}}}',
          f'\\newcommand{{\\jusSoJusante}}{{{NUM[len(L0)-naud]}}}']
         + L)
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(L0)} operacoes, mediana {med:.1f} %, piso {piso} % -> {SAIDA.name}')


if __name__ == '__main__':
    main()
