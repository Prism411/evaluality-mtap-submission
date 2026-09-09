#!/usr/bin/env python3
"""Figura: trocar o modulo muda o resumo, medido SEM modelo de referencia.

⭐ Esta e a comparacao que o desenho de bancada permite e que nenhum dos artigos de
origem pode fazer: as mesmas 42 decisoes, o mesmo pipeline, so o modulo trocado.
Nao ha referencia envolvida — a pergunta e apenas se as escolhas coincidem."""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'fig_menu.tex'
NOME = {'brilho': 'Brightness', 'huang_exposicao': 'Exposure', 'ke_brightness': 'Brightness (K.)',
        'hasler_colorfulness': 'Colourfulness (H.)', 'ke_colorfulness': 'Colourfulness (K.)',
        'contraste_variancia': 'Contrast variance', 'huang_matiz': 'Hue', 'huang_saturacao': 'Saturation',
        'ke_contraste': 'Contrast', 'ke_edge_distribution': 'Edge distribution',
        'ke_hue_count': 'Hue count', 'laplacian_var': 'Laplacian variance',
        'sobel_cv': 'Sobel CV', 'srinivas_quality': 'Composite of five'}


POREXT = {11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
          15: 'fifteen', 16: 'sixteen'}


def main():
    cla = json.load(open(QB / 'a_classe_nao_concorda_consigo.json'))
    d = json.load(open(QB / 'jusante_completo_sem_sift.json'))
    g = d['agrupamento']
    pares = d['concordancia_par_a_par']
    piso = d['piso_do_acaso_pct']
    grupos = sorted(g.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    L = [r'\begin{figure}[!ht]', r'\centering',
         r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]']
    # ── esquerda: os 11 resumos distintos
    y = 0.0
    L.append(r'\node[anchor=west,font=\scriptsize\bfseries,text=headerblue] at (0,0.52) '
             r'{11 distinct summaries};')
    for i, (k, membros) in enumerate(grupos):
        h = 0.30 + 0.02
        L.append(f'\\fill[{"accentorange!22" if len(membros)>1 else "rowlight"}] '
                 f'(0,{y-h:.2f}) rectangle (5.55,{y-0.03:.2f});')
        rot = ', '.join(NOME.get(m, m) for m in membros)
        L.append(f'\\node[anchor=west,font=\\scriptsize] at (0.10,{y-h/2-0.015:.2f}) '
                 f'{{{rot[:56]}}};')
        if len(membros) > 1:
            L.append(f'\\node[anchor=east,font=\\scriptsize\\bfseries,text=accentorange!80!black]'
                     f' at (5.50,{y-h/2-0.015:.2f}) {{$\\times${len(membros)}}};')
        y -= h + 0.055
    # ── direita: a distribuicao das concordancias par a par
    vals = sorted(float(v if not isinstance(v, dict) else v.get('pct', 0))
                  for v in pares.values())
    x0, W = 6.35, 4.0
    L.append(r'\node[anchor=west,font=\scriptsize\bfseries,text=headerblue] at '
             f'({x0:.2f},0.52) {{agreement of the 91 pairs}};')
    top = y
    for j, v in enumerate(vals):
        yy = -0.03 - j * (abs(top) / max(len(vals), 1))
        cor = 'accentred!55' if v < piso else 'accentgreen!30'
        L.append(f'\\fill[{cor}] ({x0:.2f},{yy-0.028:.3f}) rectangle '
                 f'({x0+W*v/100:.2f},{yy:.3f});')
    for t in (0, 25, 50, 75, 100):
        L.append(f'\\node[font=\\scriptsize,text=black!50] at '
                 f'({x0+W*t/100:.2f},{top-0.22:.2f}) {{{t}}};')
    L.append(f'\\draw[accentred,line width=.8pt,dash pattern=on 2pt off 1.6pt] '
             f'({x0+W*piso/100:.2f},0.30) -- ({x0+W*piso/100:.2f},{top-0.06:.2f});')
    L.append(f'\\node[anchor=north,font=\\scriptsize,text=accentred!80!black] at '
             f'({x0+W*piso/100:.2f},{top-0.34:.2f}) {{chance {piso:.0f}}};')
    L += [r'\end{tikzpicture}',
          # ⛔ toda contagem da legenda sai do JSON medido. O `2.21` estava DIGITADO:
          # conferia com a fonte, mas nao acompanharia uma mudanca dela.
          f'\\caption{{The same {d["n_clusters"]} redundancy clusters, the same pipeline, '
          f'only the visual-selection operation swapped; no reference model is involved. '
          f'\\textbf{{Left}}: {POREXT[d["n_operacoes"]]} operations produce '
          f'{POREXT[d["resumos_distintos"]]} distinct summaries, and only two groups agree '
          f'completely: the three brightness variants and the two colourfulness '
          f'implementations. \\textbf{{Right}}: agreement for each of the {d["n_pares"]} '
          f'operation pairs, sorted, against the chance floor of ${d["piso_do_acaso_pct"]:.0f}$ '
          f'per cent. Every cluster has at least two operations choosing differently, the '
          f'average cluster draws ${d["escolhas_distintas_por_cluster_media"]:.2f}$ distinct '
          f'choices, and \\textbf{{{d["pares_abaixo_do_piso"]} of the {d["n_pares"]} pairs '
          f'agree below chance}}. \\textbf{{Pairs drawn from the same source work agree no '
          f'more than pairs from different works}}: median $\\kappa$ '
          f'{cla["mesma_fonte_contra_fontes_diferentes"]["dentro"]["mediana"]:.3f}'.replace("0.", ".") + f' over '
          f'{cla["mesma_fonte_contra_fontes_diferentes"]["dentro"]["n"]} within-work pairs '
          f'against ' + f'{cla["mesma_fonte_contra_fontes_diferentes"]["fora"]["mediana"]:.3f}'.replace("0.", ".") + f' over '
          f'{cla["mesma_fonte_contra_fontes_diferentes"]["fora"]["n"]} across-work pairs, '
          f'with the two exact duplicates excluded. The choice of operation is not a detail '
          f'of the stage; it is most of what the stage decides.}}',
          r'\label{fig:menu}', r'\end{figure}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(grupos)} grupos, {len(vals)} pares -> {SAIDA.name}')


if __name__ == '__main__':
    main()
