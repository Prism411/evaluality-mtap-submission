#!/usr/bin/env python3
"""Figura 1: matriz de inversao. 15 operacoes da literatura x 8 degradacoes.
Cor = acuracia pareada. Vermelho = prefere a copia DEGRADADA."""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'fig_inversao.tex'
TIPOS = ['Darken', 'Motion', 'Blur', 'H.264', 'Rescale', 'Satur.', 'Noise', 'JPEG']
NOME = {'ke_edge_distribution': 'Edge distribution', 'qaroush_go': 'Gradient orientation',
        'ke_contraste': 'Contrast', 'contraste_variancia': 'Contrast variance',
        'ke_hue_count': 'Hue count', 'qaroush_entropia': 'Entropy',
        'qaroush_gm': 'Gradient magnitude', 'qaroush_saliencia': 'Saliency area',
        'gygli_media_crua': 'Averaged aesthetics (3)', 'srinivas_quality': 'Composite of five',
        'glcm_contraste': 'GLCM contrast', 'laplacian_var': 'Laplacian variance',
        'huang_saturacao': 'Saturation', 'hasler_colorfulness': 'Colourfulness (Hasler)',
        'ke_colorfulness': 'Colourfulness (Ke)'}


def cor(a):
    """Vermelho abaixo de 50 (prefere o degradado), verde acima."""
    if a < 50:
        f = max(0.0, min(1.0, (50 - a) / 50))
        return f'accentred!{int(18 + 62 * f)}'
    f = max(0.0, min(1.0, (a - 50) / 50))
    return f'accentgreen!{int(10 + 45 * f)}'


def main():
    A16 = set(json.load(open(QB / 'proveniencia_das_operacoes.json'))
              ['as_16_da_tabela_de_triagem'])
    d = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
    ops = [o for o in A16 if d.get(o) and d[o].get('direcao_maior_melhor') is not None
           and not any(x is None for x in d[o]['acuracia_por_tipo'])]
    # ordena pelo pior caso: quem inverte mais forte no topo
    ops.sort(key=lambda o: min(d[o]['acuracia_por_tipo']))
    cw, ch = 1.02, 0.365
    L = [r'\begin{figure}[!ht]', r'\centering',
         r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]']
    for j, tp in enumerate(TIPOS):
        L.append(f'\\node[rotate=42,anchor=west,font=\\scriptsize\\bfseries] at '
                 f'({j*cw+0.30:.2f},{0.16:.2f}) {{{tp}}};')
    for i, o in enumerate(ops):
        y = -(i + 1) * ch
        L.append(f'\\node[anchor=east,font=\\scriptsize] at (-0.14,{y+ch/2:.2f}) '
                 f'{{{NOME.get(o,o)}}};')
        for j, a in enumerate(d[o]['acuracia_por_tipo']):
            x = j * cw
            L.append(f'\\fill[{cor(a)}] ({x:.2f},{y:.2f}) rectangle '
                     f'({x+cw-0.05:.2f},{y+ch-0.05:.2f});')
            neg = a < 50
            L.append(f'\\node[font=\\scriptsize{"\\bfseries" if neg else ""},'
                     f'text={"accentred!75!black" if neg else "black!70"}] at '
                     f'({x+(cw-0.05)/2:.2f},{y+(ch-0.05)/2:.2f}) {{{a:.0f}}};')
    yb = -(len(ops) + 1) * ch - 0.16
    L += [f'\\draw[rulegray,line width=.4pt] (-0.06,{yb+0.30:.2f}) -- '
          f'({len(TIPOS)*cw-0.05:.2f},{yb+0.30:.2f});',
          f'\\fill[accentred!60] (0,{yb-0.06:.2f}) rectangle (0.30,{yb+0.16:.2f});',
          f'\\node[anchor=west,font=\\scriptsize] at (0.36,{yb+0.05:.2f}) '
          f'{{below 50: the operation ranks the \\emph{{degraded}} copy higher}};',
          r'\end{tikzpicture}',
          r'\caption{Paired accuracy of each summarization heuristic on 800 '
          r'unmodified--degraded broadcast pairs. Each cell is 100 '
          r'pairs, 20 segments at five severity levels, and the better member is fixed by '
          r'construction. \textbf{Every operation falls below chance on at least one '
          r'type, and thirteen of the fifteen do so under white noise}, five of them on '
          r'every pair. Rows are ordered by worst cell.}',
          r'\label{fig:inversion}', r'\end{figure}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(ops)} operacoes x {len(TIPOS)} tipos -> {SAIDA.name}')


if __name__ == '__main__':
    main()
