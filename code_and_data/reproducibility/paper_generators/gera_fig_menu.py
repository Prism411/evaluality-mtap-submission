#!/usr/bin/env python3
"""Figura: trocar o modulo muda o resumo, medido SEM modelo de referencia.

⭐ Esta e a comparacao que o desenho de bancada permite e que nenhum dos artigos de
origem pode fazer: as mesmas 42 decisoes, o mesmo pipeline, so o modulo trocado.
Nao ha referencia envolvida — a pergunta e apenas se as escolhas coincidem."""
import os
import json
import re
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'fig_menu.tex'
NOME = {'brilho': 'Brightness', 'huang_exposicao': 'Exposure', 'ke_brightness': r'Brightness~\citep{ke2006highlevel}',
        'hasler_colorfulness': r'Colourfulness~\citep{hasler2003colorfulness}', 'ke_colorfulness': r'Colourfulness~\citep{ke2006highlevel}',
        # ⚠️ «Hue» e «Hue count» sem fonte pareciam a mesma operacao; a figura ja usa
        # «(H.)» e «(K.)» nas outras duplicatas, entao estas seguem o mesmo estilo.
        'contraste_variancia': 'Grey-level dispersion', 'huang_matiz': r'Hue~\citep{huang2024aesthetic}',
        'huang_saturacao': 'Saturation',
        'ke_contraste': 'Contrast', 'ke_edge_distribution': 'Edge distribution',
        'ke_hue_count': r'Hue count~\citep{ke2006highlevel}', 'laplacian_var': 'Laplacian variance',
        'sobel_cv': 'Sobel CV', 'srinivas_quality': 'Composite of five',
        # ⭐ 21/09: as sete que faltavam quando a figura passou de 14 para 21 operacoes
        'glcm_contraste': 'GLCM contrast', 'gygli_media_crua': 'Averaged aesthetics (3)',
        'qaroush_ct': 'Contrast term', 'qaroush_entropia': 'Entropy',
        'qaroush_gm': 'Gradient magnitude', 'qaroush_go': 'Gradient orientation',
        'qaroush_saliencia': 'Saliency area'}


POREXT = {11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
          15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
          19: 'nineteen', 20: 'twenty', 21: 'twenty-one'}


def corta(rot, limite=74):
    """Encurta o rotulo SEM cortar dentro de uma macro.

    ⛔ o corte anterior era `rot[:56]`, por caractere. Quando os rotulos
    passaram a trazer `\\citep{...}`, ele partia a macro ao meio e o grupo de
    chaves ficava aberto: o LaTeX so dizia «perhaps a missing \\item».
    """
    if len(rot) <= limite:
        return rot
    corte = rot[:limite]
    # nao termina dentro de um grupo de chaves nem de um nome de macro
    if corte.count('{') != corte.count('}') or re.search(r'\\[A-Za-z]*$', corte):
        corte = corte[:corte.rfind(',')] if ',' in corte else rot
    return corte


def main():
    cla = json.load(open(QB / 'a_classe_nao_concorda_consigo.json'))
    con = json.load(open(QB / 'a_contabilidade_dos_91_pares_fecha.json'))
    # ⛔ 21/09: esta figura lia `jusante_completo_sem_sift.json`, de 05/09, que so enxerga
    # as 14 operacoes do `efeito_a_jusante.json`. A manchete de 4.6 ja falava em 21 -> 18,
    # e o corpo carregava os dois universos sem reconciliar. Passa a ler o mesmo arquivo da
    # manchete. ⚠️ As 14 eram SUBCONJUNTO ESTRITO das 21, entao nao e medicao nova.
    d0 = json.load(open(QB / 'quantos_resumos_distintos_a_classe_produz.json'))
    if not d0.get('controle_passou'):
        raise SystemExit('⛔ o controle das identidades declaradas REPROVOU na fonte')
    t0, pp = d0['todas_as_operacoes'], d0['par_a_par']
    d = {'n_clusters': d0['n_clusters'], 'n_operacoes': t0['n_operacoes'],
         'resumos_distintos': t0['n_resumos_distintos'], 'n_pares': pp['n_pares'],
         'piso_do_acaso_pct': d0['piso_do_acaso_pct'],
         'pares_abaixo_do_piso': pp['abaixo_do_piso'],
         'escolhas_distintas_por_cluster_media':
             d0['escolhas_distintas_por_cluster_media']}
    g = t0['grupos']
    pares = pp['pares']
    piso = d['piso_do_acaso_pct']
    grupos = sorted(g.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    # ⛔ operacao sem rotulo sairia com a chave crua do JSON na figura publicada
    faltam = sorted({m for _, ms in grupos for m in ms} - set(NOME))
    if faltam:
        raise SystemExit(f'⛔ {len(faltam)} operacao(oes) sem nome de exibicao: {faltam}')
    L = [r'\begin{figure}[!ht]', r'\centering',
         r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]']
    # ── esquerda: os 11 resumos distintos
    y = 0.0
    # ⛔ o «11» estava DIGITADO neste cabecalho e nao acompanhou a expansao do inventario
    L.append(r'\node[anchor=west,font=\scriptsize\bfseries,text=headerblue] at (0,0.52) '
             f'{{\\textbf{{(a)}}\\enspace{d["resumos_distintos"]} distinct representative '
             f'selections}};')
    for i, (k, membros) in enumerate(grupos):
        h = 0.30 + 0.02
        L.append(f'\\fill[{"accentorange!22" if len(membros)>1 else "rowlight"}] '
                 f'(0,{y-h:.2f}) rectangle (5.55,{y-0.03:.2f});')
        rot = ', '.join(NOME.get(m, m) for m in membros)
        L.append(f'\\node[anchor=west,font=\\scriptsize] at (0.10,{y-h/2-0.015:.2f}) '
                 f'{{{corta(rot)}}};')
        if len(membros) > 1:
            # ⛔ 22/09: ancorado a LESTE em 6.15 o «xN» encostava no rotulo mais longo
            #    (6,2 pt de folga contra os 8 exigidos) e a coluna da direita comeca em
            #    6.35. Ancorado a OESTE logo depois da barra ele fica longe dos dois.
            L.append(f'\\node[anchor=west,font=\\scriptsize\\bfseries,text=accentorange!80!black]'
                     f' at (5.66,{y-h/2-0.015:.2f}) {{$\\times${len(membros)}}};')
        y -= h + 0.055
    # ── direita: a distribuicao das concordancias par a par
    vals = sorted(float(v if not isinstance(v, dict) else v.get('pct', 0))
                  for v in pares.values())
    x0, W = 6.95, 3.9
    L.append(r'\node[anchor=west,font=\scriptsize\bfseries,text=headerblue] at '
             f'({x0:.2f},0.52) {{\\textbf{{(b)}}\\enspace agreement of the {d["n_pares"]} '
             f'pairs}};')
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
          # ⭐ 21/09: legenda ENXUTA (criterio 30 e FG02). A anterior tinha 150 palavras
          # e fechava com uma conclusao retorica; o painel within/across foi para o texto.
          f'\\caption{{The same {d["n_clusters"]} redundancy clusters and the same '
          f'pipeline, with only the visual-selection operation swapped; \\textbf{{no '
          f'reference model is involved}}. \\textbf{{(a)}}: the {POREXT[d["n_operacoes"]]} '
          f'operations grouped by the representative set each produces, giving '
          f'{POREXT[d["resumos_distintos"]]} \\emph{{distinct sets}}; a group of more than one '
          f'operation carries its size as a multiplier. '
          f'\\textbf{{(b)}}: '
          f'agreement '
          # ⛔ 22/09 (parecer v2): eram UNORDERED. C(21,2)=210; ordenados seriam 420.
          f'for each of the {d["n_pares"]} \\emph{{unordered operation pairs}}, sorted, '
          f'against the chance floor of ${d["piso_do_acaso_pct"]:.0f}$ per cent (dashed); '
          f'\\textbf{{{d["pares_abaixo_do_piso"]} pairs agree below chance}}. The only '
          f'groups that agree completely are operations computing the same quantity: the '
          f'brightness variants and the two colourfulness implementations. '
          f'\\textbf{{SIFT+BoVW is absent from this panel by design}}: every operation here '
          f'scores the same input regime, and its key-frame selector is part of the '
          f'published method, so holding the input fixed would evaluate a different '
          f'operation. The matched-input control of Section~4.6 is the diagnostic that '
          f'compares it under a common interface. '
          # ⭐ 22/09 (parecer v2, V2-071): os rotulos tinham de ser decodificaveis sem
          # abrir o suplementar, e a ordenacao das barras nao torna o par ordenado.
          f'\\emph{{Labels}}: CV, coefficient of variation; GLCM, '
          f'grey-level co-occurrence matrix. Rows that name the same attribute '
          f'carry the reference of the work that defines it.}}',
          r'\label{fig:menu}', r'\end{figure}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(grupos)} grupos, {len(vals)} pares -> {SAIDA.name}')


if __name__ == '__main__':
    main()
