#!/usr/bin/env python3
"""Figura 2: a acuracia media da classe por degradacao, ordenada, com as que ADICIONAM
estrutura separadas das que REMOVEM. E o argumento fisico do artigo, num grafico."""
import os
import json
import statistics as st
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'fig_direcao.tex'
# ⛔ A ORDEM E A DOS DADOS, nao uma escolha de apresentacao. Eu tinha trocado
#    satur/noise/jpeg aqui e a figura saiu com rotulo colado no valor errado:
#    dizia «White noise 62,9» quando o ruido e 19,1. O indice j indexa o vetor
#    `acuracia_por_tipo`, entao esta lista TEM de segui-lo.
# ⛔ A classe de cada degradacao NAO e escolha minha: vem de `energia_por_tipo.json`,
#    que mede a razao mediana de energia de alta frequencia ao original. Eu tinha posto
#    o JPEG como «adiciona» por intuicao e a medicao diz 0,950, ou seja REMOVE. So o
#    ruido adiciona, e por um fator de 6,9.
T = [('dark', 'Darkening'), ('motion', 'Motion blur'), ('blur', 'Gaussian blur'),
     ('h264', 'H.264'), ('rescale', 'Rescaling'), ('satur', 'Desaturation'),
     ('noise', 'White noise'), ('jpeg', 'JPEG')]


POREXT = {5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight'}


def main():
    A16 = set(json.load(open(QB / 'proveniencia_das_operacoes.json'))
              ['as_16_da_tabela_de_triagem'])
    d = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
    ops = [o for o in sorted(A16) if d.get(o) and d[o].get('direcao_maior_melhor') is not None
           and not any(x is None for x in d[o]['acuracia_por_tipo'])]
    en = json.load(open(QB / 'energia_por_tipo.json'))['energia_por_tipo']
    linhas = []
    for j, (k, rot) in enumerate(T):
        v = [d[o]['acuracia_por_tipo'][j] for o in ops]
        r = en[k]['razao_mediana_ao_original']
        cls = 'add' if en[k]['adiciona_energia'] else 'rem'
        linhas.append((rot, cls, st.mean(v), sum(1 for x in v if x < 50), v, r))
    linhas.sort(key=lambda x: -x[2])
    # ⛔ os tres numeros da legenda saiam DIGITADOS. Vem das mesmas linhas da figura.
    _ruido = [L_ for L_ in linhas if L_[1] == 'add'][0]
    _fator, _media, _mediana = _ruido[5], _ruido[2], st.median(_ruido[4])
    _reduzem = sum(1 for L_ in linhas if L_[1] == 'rem')
    W, bh, gap = 7.4, 0.40, 0.20
    COR = {'add': 'accentred', 'rem': 'accentgreen', 'mix': 'accentorange'}
    L = [r'\begin{figure}[!ht]', r'\centering',
         r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]']
    # eixo
    for x in (0, 25, 50, 75, 100):
        px = x / 100 * W
        L.append(f'\\draw[rulegray!45,line width=.3pt] ({px:.2f},0.28) -- '
                 f'({px:.2f},{-(len(linhas))*(bh+gap):.2f});')
        L.append(f'\\node[font=\\scriptsize,text=black!55] at ({px:.2f},0.48) {{{x}}};')
    L.append(f'\\draw[accentred,line width=.8pt,dash pattern=on 2pt off 1.6pt] '
             f'({50/100*W:.2f},0.28) -- ({50/100*W:.2f},{-(len(linhas))*(bh+gap):.2f});')
    for i, (rot, cls, m, ab, v, r) in enumerate(linhas):
        y = -(i + 1) * (bh + gap) + gap
        L.append(f'\\node[anchor=east,font=\\scriptsize] at (-0.16,{y+bh/2:.2f}) {{{rot}}};')
        L.append(f'\\fill[{COR[cls]}!{30 if cls!="add" else 55}] (0,{y:.2f}) rectangle '
                 f'({m/100*W:.2f},{y+bh:.2f});')
        # pontos individuais
        for x in v:
            L.append(f'\\fill[black!42] ({x/100*W:.2f},{y+bh/2:.2f}) circle (0.036);')
        L.append(f'\\node[anchor=west,font=\\scriptsize\\bfseries,'
                 f'text={COR[cls]}!75!black] at ({m/100*W+0.12:.2f},{y+bh/2:.2f}) '
                 f'{{{m:.1f}}};')
        L.append(f'\\node[anchor=west,font=\\scriptsize,text=black!50] at '
                 f'({W+0.62:.2f},{y+bh/2:.2f}) {{{ab}/15}};')
        L.append(f'\\node[anchor=west,font=\\scriptsize,'
                 f'text={"accentred!75!black" if cls=="add" else "black!45"}] at '
                 f'({W+1.55:.2f},{y+bh/2:.2f}) {{{r:.2f}$\\times$}};')
    yb = -(len(linhas) + 1) * (bh + gap)
    L += [f'\\node[anchor=west,font=\\scriptsize\\bfseries,text=black!55] at '
          f'({W+0.62:.2f},{0.48:.2f}) {{$<$50}};',
          f'\\node[anchor=west,font=\\scriptsize\\bfseries,text=black!55] at '
          f'({W+1.85:.2f},{0.48:.2f}) {{HF en.}};',
          f'\\fill[accentgreen!30] (0,{yb:.2f}) rectangle (0.26,{yb+0.20:.2f});',
          f'\\node[anchor=west,font=\\scriptsize] at (0.32,{yb+0.10:.2f}) '
          f'{{removes it}};',
          f'\\fill[accentred!55] (3.6,{yb:.2f}) rectangle (3.86,{yb+0.20:.2f});',
          f'\\node[anchor=west,font=\\scriptsize] at (3.92,{yb+0.10:.2f}) '
          f'{{adds high-frequency energy}};',
          r'\end{tikzpicture}',
          r'\caption{Mean paired accuracy of the fifteen summarization operations, by '
          r'degradation type; grey dots are the individual operations and the dashed line '
          r'is chance. \textbf{Rows are ordered by mean accuracy, descending.} The last '
          r'column is what each degradation does to local image high-frequency energy, '
          f'measured as the median ratio to the original. For the {POREXT[_reduzem]} '
          f'transformations that reduce it, mean paired accuracy exceeds 50 per cent and '
          f'the displayed median ratio is at most 1.00. \\textbf{{White noise is '
          f'the only one that raises it}}, by a factor of ${_fator:.1f}$, and it is answered '
          f'at ${_media:.1f}$ per cent with a median of ${_mediana:.1f}$. The middle column '
          f'counts operations below chance.}}',
          r'\label{fig:direction}', r'\end{figure}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(linhas)} degradacoes -> {SAIDA.name}')


if __name__ == '__main__':
    main()
