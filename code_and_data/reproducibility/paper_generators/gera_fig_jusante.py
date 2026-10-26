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
NOME = {'qaroush_ct': 'Contrast term', 'sobel_cv': 'Sobel variation coeff.', 'contraste_variancia': 'Grey-level dispersion',
        'laplacian_var': 'Laplacian variance', 'huang_exposicao': 'Exposure',
        'brilho': 'Brightness', 'ke_brightness': 'Brightness (Ke)',
        'ke_contraste': 'Contrast (Ke)', 'hasler_colorfulness': 'Colourfulness (Hasler)',
        'ke_colorfulness': 'Colourfulness (Ke)', 'srinivas_quality': 'Composite of five',
        # ⚠️ «Hue count» e «Hue» em linhas vizinhas pareciam a mesma operacao duas vezes.
        # A figura ja usa o padrao «(Ke)»/«(Hasler)» nas outras duas duplicatas.
        'huang_saturacao': 'Saturation (Huang)', 'huang_matiz': 'Hue (Huang)',
        'ke_edge_distribution': 'Edge distribution (Ke)', 'ke_hue_count': 'Hue count (Ke)',
        # ⭐ 21/09: as que fechavam a lacuna de cobertura a jusante
        'qaroush_entropia': 'Entropy', 'qaroush_saliencia': 'Saliency area',
        'glcm_contraste': 'GLCM contrast', 'gygli_media_crua': 'Averaged aesthetics (3)',
        'qaroush_gm': 'Gradient magnitude', 'qaroush_go': 'Gradient orientation'}


def main():
    d = json.load(open(QB / 'jusante_lado_a_lado.json'))
    # ⛔ as 14 do jusante NAO sao as 16 auditadas: 5 delas nunca passaram pela triagem
    aud = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    L0 = [x for x in d['linhas'] if 'sumarizacao' in x['familia']]
    # ⭐ 21/09: entram as sete que faltavam, remedidas pelo CAMINHO PUBLICADO
    # (`jusante_ops_faltantes_caminho_velho.json`), com controle dentro da rodada:
    # quatro operacoes ja publicadas reproduzem 42/42 o vencedor registrado.
    # ⛔ NAO se usa `jusante_ops_novas.json`, medido por outro decodificador: o
    # controle declarado antes reprovou e dois dos seis valores divergem por um cluster.
    _ja = {x['nome'] for x in L0}
    _novas = json.load(open(
        QB / 'jusante_ops_faltantes_caminho_velho.json'))['concordancia_com_sift']
    for nome, v in _novas.items():
        # ⭐ 22/09: o `qaroush_ct` VOLTA. Ele nao esta entre as quinze auditadas, mas
        # tem retencao medida nos mesmos 42 clusters e ja aparece na Figura 2 e na
        # Tabela 6; deixa-lo fora so daqui e que produzia dois inventarios.
        if nome in _ja or nome not in NOME:
            continue
        L0.append({'nome': nome, 'familia': 'operacao de sumarizacao',
                   'concorda': v['concorda'], 'n': v['n'], 'pct': v['pct']})
    L0.sort(key=lambda z: -z['pct'])
    piso, n = d['piso_do_acaso_pct'], d['n_clusters']
    # ⛔ e a figura so vale se TODAS vierem dos mesmos clusters
    assert all(x['n'] == n for x in L0), \
        f'⛔ populacao diferente entre operacoes: {sorted({x["n"] for x in L0})}'
    assert len(L0) == 21, len(L0)
    # ⭐ 22/09 (parecer v5, 2.5): as barras estavam comprimidas e a pagina tinha folga.
    W, bh, gap = 5.3, 0.268, 0.056
    COLNUM = W + 0.32                       # ⭐ os numeros saem da area do grafico: dentro
    base = -(len(L0)) * (bh + gap) - 0.10   # dela colidiam com a grade e com as verticais
    L = [r'\begin{figure}[!ht]', r'\centering',
         r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]']
    for x in (0, 25, 50, 75, 100):
        px = x / 100 * W
        L += [f'\\draw[rulegray!30,line width=.3pt] ({px:.2f},0.16) -- ({px:.2f},{base:.2f});',
              f'\\node[font=\\scriptsize,text=black!62] at ({px:.2f},0.36) {{{x}}};']
    L.append(f'\\draw[accentred!85,line width=.9pt,dash pattern=on 2pt off 1.5pt] '
             f'({piso/100*W:.2f},0.16) -- ({piso/100*W:.2f},{base:.2f});')
    for i, x in enumerate(L0):
        y = -(i + 1) * (bh + gap) + gap
        ab = x['pct'] < piso
        L += [f'\\node[anchor=east,font=\\scriptsize] at (-0.14,{y+bh/2:.2f}) '
              f'{{{NOME[x["nome"]]}}};',
              f'\\fill[{"accentred!70" if ab else "focoauditado!45"}] (0,{y:.2f}) rectangle '
              f'({x["pct"]/100*W:.2f},{y+bh:.2f});',
              f'\\node[anchor=west,font=\\scriptsize,text=black!'
              f'{"82" if ab else "72"}] at ({COLNUM:.2f},{y+bh/2:.2f}) '
              f'{{{x["concorda"]}/{x["n"]} \\ ({x["pct"]:.1f}\\%)}};']
    med = st.median([x['pct'] for x in L0])
    ab = [x for x in L0 if x['pct'] < piso]
    NUM = {21: 'twenty-one', 20: 'twenty', 19: 'nineteen', 18: 'eighteen', 17: 'seventeen', 16: 'sixteen',
           15: 'fifteen', 14: 'fourteen', 13: 'thirteen', 12: 'twelve', 11: 'eleven',
           10: 'ten', 9: 'nine', 8: 'eight', 7: 'seven', 6: 'six', 5: 'five', 4: 'four',
           3: 'three', 2: 'two', 1: 'one', 0: 'none'}
    nomes = [x['nome'] for x in L0]
    naud = sum(1 for k in nomes if k in aud)
    eleg = sum(1 for k in nomes if k in aud and aud[k].get('elegivel'))
    assert eleg == 0, f'⛔ {eleg} das auditadas sao elegiveis: a frase da prosa cai'
    L += [f'\\fill[black!72] ({med/100*W-0.07:.2f},0.60) -- ({med/100*W+0.07:.2f},0.60) -- '
          f'({med/100*W:.2f},0.46) -- cycle;',
          f'\\node[anchor=south,font=\\scriptsize,text=black!72] at '
          f'({med/100*W:.2f},0.62) {{median {med:.1f}\\%}};',
          f'\\node[anchor=north,font=\\scriptsize,text=accentred!80!black] at '
          f'({piso/100*W:.2f},{base-0.06:.2f}) {{baseline {piso:.0f}\\%}};',
          r'\end{tikzpicture}',
          r'\caption{Selected-segment retention under alternative implementations of the '
          r'quality criterion. Only the scoring implementation is replaced; the bar is the '
          rf'percentage of the {n} redundancy-cluster representatives that survive the swap. '
          rf'\textbf{{The median operation keeps {med:.1f} per cent of the decisions against '
          rf'a uniform-choice baseline of {piso:.0f}}}, and the {NUM[len(ab)]} in red keep fewer than '
          r'chance. '
          rf'Retention ranges from {min(x["pct"] for x in L0):.0f} to '
          rf'{max(x["pct"] for x in L0):.0f} per cent. The clusters are shared '
          rf'across all {NUM[len(L0)]} operations and the SIFT+BoVW one; \textbf{{the '
          r'frames are not}: the per-frame operations score one frame per second, while '
          r'SIFT+BoVW runs its own internal key-frame selector.}',
          r'\label{fig:jusante}', r'\end{figure}']
    # ⚠️ «hue count, hue» lado a lado na prosa parece a mesma operacao duas vezes.
    # Sao duas: a contagem de matizes do Ke e o termo de matiz do Huang.
    nom = {'qaroush_ct': "Qaroush's contrast term", 'ke_hue_count': "Ke's hue count", 'huang_matiz': "Huang's hue",
           'ke_edge_distribution': 'edge distribution', 'huang_saturacao': 'saturation',
           'qaroush_entropia': 'entropy', 'qaroush_saliencia': 'saliency area',
           'glcm_contraste': 'GLCM contrast', 'gygli_media_crua': 'averaged aesthetics',
           'qaroush_gm': 'gradient magnitude', 'qaroush_go': 'gradient orientation',
           'sobel_cv': "Sobel variation coefficient", 'laplacian_var': 'Laplacian variance',
           'contraste_variancia': 'grey-level dispersion', 'brilho': 'brightness',
           'ke_brightness': "Ke's brightness", 'huang_exposicao': 'exposure',
           'ke_contraste': "Ke's contrast", 'hasler_colorfulness': 'colourfulness',
           'ke_colorfulness': "Ke's colourfulness", 'srinivas_quality': 'composite of five'}
    # ⛔ a lista de nomes da prosa precisa cobrir TODA operacao que possa cair abaixo do
    # acaso, nao so as que caiam hoje. Antes ela tinha quatro entradas e uma operacao
    # nova abaixo do piso quebraria a geracao com KeyError, que e o modo bom de falhar,
    # mas so depois de alguem rodar.
    _sem_nome = [x['nome'] for x in ab if x['nome'] not in nom]
    assert not _sem_nome, f'⛔ sem nome de prosa: {_sem_nome}'
    ext = ', '.join(nom[x['nome']] for x in sorted(ab, key=lambda z: z['pct']))
    # ⛔ 21/09: a prosa de 4.6 dizia «Of the fourteen» com DIGITO DIGITADO enquanto esta
    # figura ja imprimia «all twenty operations» duas linhas acima, e a propria frase
    # seguinte somava \jusAuditadas (fifteen) + \jusSoJusante (five). O total passa a sair
    # daqui, senao o defeito volta na proxima expansao do inventario.
    # ⛔ 21/09: as macros saem para ARQUIVO PROPRIO, carregado antes do `\begin{document}`.
    # Enquanto viviam dentro de `fig_jusante.tex`, elas so existiam a partir do ponto em
    # que a figura entra por `\input`, e a figura so podia ficar onde esta: descer a figura
    # para o suplementar deixaria as SETE ocorrencias do corpo com «Undefined control
    # sequence» e numero VAZIO no PDF, com o erro escondido no log. Ja aconteceu com
    # `\jusMediana` e `\jusPiso` no resumo.
    MACROS = [f'\\newcommand{{\\jusTotal}}{{{NUM[len(L0)]}}}',
              f'\\newcommand{{\\jusAbaixo}}{{{NUM[len(ab)]}}}',
              f'\\newcommand{{\\jusAbaixoNomes}}{{{ext}}}',
              f'\\newcommand{{\\jusMediana}}{{{med:.1f}}}',
              f'\\newcommand{{\\jusPiso}}{{{piso:.1f}}}',
              f'\\newcommand{{\\jusMin}}{{{min(x["pct"] for x in L0):.1f}}}',
              f'\\newcommand{{\\jusMax}}{{{max(x["pct"] for x in L0):.1f}}}',
              f'\\newcommand{{\\jusReescreveMin}}{{{100-max(x["pct"] for x in L0):.0f}}}',
              f'\\newcommand{{\\jusReescreveMax}}{{{100-min(x["pct"] for x in L0):.0f}}}',
              f'\\newcommand{{\\jusAuditadas}}{{{NUM[naud]}}}',
              f'\\newcommand{{\\jusSoJusante}}{{{NUM[len(L0)-naud]}}}']
    (SAIDA.parent / 'macros_jusante.tex').write_text('\n'.join(MACROS) + '\n')
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(L0)} operacoes, mediana {med:.1f} %, piso {piso} % -> {SAIDA.name}'
          f' + macros_jusante.tex')


if __name__ == '__main__':
    main()
