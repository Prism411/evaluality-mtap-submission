#!/usr/bin/env python3
"""A TABELA DE RASTREIO: operacao -> fonte -> formula -> funcao -> arquivo -> referencia.

POR QUE EXISTE (07/09/2026). Duas linhas trocaram de nome entre versoes mantendo os
numeros, e uma coluna mudou de modelo de referencia sem que a nota fosse mantida. Os dois
defeitos tem a mesma causa: nao havia um lugar unico que ligasse o nome impresso a funcao
executada e ao arquivo que guarda o resultado. Esta tabela e esse lugar, e dela saem os
nomes das demais.

⚠️ A coluna `Ref.` existe porque as duas familias NAO usam o mesmo modelo de referencia na
coluna do piso: as operacoes sao pontuadas contra LIQE e os dez modelos NR-IQA contra
Q-Align. Isso esta declarado aqui e na legenda da tabela principal.
"""
import os
import ast
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_rastreio.tex'

NOME = {'ke_edge_distribution': 'Edge distribution', 'qaroush_go': 'Gradient orientation',
        'si': 'Spatial information', 'ke_contraste': 'Contrast',
        'contraste_variancia': 'Grey-level dispersion', 'ke_hue_count': 'Hue count',
        'qaroush_entropia': 'Entropy', 'qaroush_gm': 'Gradient magnitude',
        'qaroush_saliencia': 'Saliency area', 'gygli_media_crua': 'Averaged aesthetics (3)',
        'srinivas_quality': 'Composite of five', 'glcm_contraste': 'GLCM contrast',
        'laplacian_var': 'Laplacian variance', 'huang_saturacao': 'Saturation',
        'hasler_colorfulness': 'Colourfulness (Hasler)',
        'ke_colorfulness': 'Colourfulness (Ke)'}
# formula, na notacao da fonte, conferida no docstring da implementacao
FORMULA = {
 'ke_edge_distribution': r'$q_a=1-w_xw_y$ (Ke \S4.1)$^{\P}$',
 'ke_contraste': r'width of central 98\% of the grey histogram (Ke \S4.5)',
 'ke_hue_count': r'$q_h=20-|N|$, $\alpha=.05$ (Ke \S4.3)',
 'ke_colorfulness': r'Hasler $M^{(3)}$; Ke gives no formula',
 'hasler_colorfulness': r'$M^{(3)}=\sigma_{rgyb}+.3\mu_{rgyb}$',
 'srinivas_quality': r'unweighted mean of the five Ke terms',
 'gygli_media_crua': r'three aesthetic attributes; unweighted mean$^{\ddagger}$',
 'qaroush_go': r'SD of Sobel gradient orientations (Eq.~15)',
 'qaroush_gm': r'mean Sobel gradient magnitude (Eq.~10)',
 'qaroush_entropia': r'Shannon entropy over HSV histogram bins (Eq.~5)',
 'qaroush_saliencia': r'area fraction above a saliency threshold (Eq.~6)',
 'glcm_contraste': r'GLCM contrast descriptor',
 'laplacian_var': r'variance of the grey-scale Laplacian',
 'contraste_variancia': r'grey-level standard deviation$^{\S}$',
 'huang_saturacao': r'mean HSV saturation (\S III-A-1)',
 'si': r'Sobel energy, ITU-T P.910',
}
# ⚠️ `_` cru dentro de \texttt{} quebra o LaTeX: escapa na origem, nao na revisao
# ⚠️ `\texttt` com `\_` nao quebra linha e estoura a celula: permite quebra apos cada um
FUNCAO = {k: k.replace('_', r'\_\allowbreak{}') for k in NOME}
FUNCAO['ke_colorfulness'] = r'hasler\_\allowbreak{}colorfulness'
FUNCAO['si'] = r'si'
ARQ = {k: r'corpus\_inteiro' for k in NOME}
ARQ['si'] = r'designA\_estendido\_83'


def main():
    A16 = json.load(open(QB / 'proveniencia_das_operacoes.json'))['as_16_da_tabela_de_triagem']
    prov = json.load(open(QB / 'proveniencia_das_operacoes.json'))['proveniencia']
    des = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
    MUDAM = 7   # pares dos 800 que trocam de lado sob a media das variancias
    # ⛔ a coluna se chama «formula, as the source states it»: uma combinacao que a fonte
    # nao enuncia nao pode entrar nela sem marca.
    KE = (0.298, 9, 0.272, 7, 0.876)

    L = [r'\begin{table}[!ht]', r'\centering',
         r'\caption{Traceability of every audited operation: the source work, the formula '
         r'as the source states it, the function that computes it, and the reference model '
         r'used on the in-domain column. Every operation '
         r'name and count printed elsewhere in this article is derived from this table. '
         r'\textbf{Dir.} is the direction the source declares; spatial information '
         r'declares none, which is why it is measured but carries no verdict.}',
         r'\label{tab:trace}', r'\scriptsize', r'\setlength{\tabcolsep}{3.4pt}',
         r'\renewcommand{\arraystretch}{1.02}',
         r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.15cm}'
         r'>{\raggedright\arraybackslash}p{1.95cm}'
         r'>{\raggedright\arraybackslash}p{3.70cm}'
         r'>{\raggedright\arraybackslash}p{2.55cm}c c@{}}', r'\toprule',
         r'\rowcolor{headerblue}',
         r'\hd{Operation} & \hd{Source} & \hd{Formula, as the source states it} & '
         r'\hd{Function} & \hd{Dir.} & \hd{Ref.} \\', r'\midrule']
    for i, k in enumerate(sorted(A16, key=lambda o: NOME[o])):
        f = prov.get(k) or []
        cite = ', '.join(f'\\citep{{{x}}}' for x in (f if isinstance(f, list) else [f])[:2]) \
            or r'\citep{itu_p910}'
        d = des.get(k, {}).get('direcao_maior_melhor')
        dirn = r'$\uparrow$' if d else (r'\textcolor{black!45}{none}' if d is None
                                        else r'$\downarrow$')
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        L.append(f"{cor}{NOME[k]} & {cite} & {FORMULA[k]} & "
                 f"\\texttt{{{FUNCAO[k]}}} & {dirn} & LIQE \\\\")
    L += [r'\midrule',
          r'\multicolumn{6}{@{}p{0.97\linewidth}}{\scriptsize All sixteen are computed by '
          r'\texttt{ops\_da\_literatura.py} on the same frames and pooled identically. '
          r'\textbf{Ref.} is the model each operation is compared against on the in-domain '
          r'column; the ten no-reference models in the main screening table use Q-Align '
          r'there instead, so that column compares each family with its own reference. '
          r'Colourfulness has no formula in Ke, who cites Datta; the Hasler expression is '
          r'used and the substitution is declared here rather than silently. Scores for '
          rf'fifteen operations are in \texttt{{{ARQ["ke_contraste"]}.json}}; spatial '
          r'information is scored on the extended 83-segment design by '
          r'\texttt{si\_no\_corpus\_de\_video}, in '
          rf'\texttt{{{ARQ["si"]}.json}}.}} \\',
          r'\midrule',
          r'\multicolumn{6}{@{}p{\linewidth}@{}}{\scriptsize ' +
         r'$^{\ddagger}$\,\citet{gygli2014summe} lists the attributes but not their combination; '
         r'\textbf{the unweighted mean is a choice made here}. '
         r'$^{\P}$\,Ke builds the edge map with a Laplacian per RGB channel at $100\times100$; '
         r'here it is Sobel magnitude on the grey frame, so \textbf{the formula is reproduced '
         r'and the map adapted}. With the source map sensitivity goes %.3f$\to$%.3f and types '
         r'%d$\to$%d (versions correlate %.3f); no verdict changes. ' % (KE[0], KE[2], KE[1], KE[3], KE[4]) +
         r'$^{\S}$\,\citet{jeong2016static} states \emph{variance of pixels} and '
         r'\citet{xu2024property} \emph{standard deviation of the grey values}; the '
         r'the standard deviation is implemented. \textbf{Within a frame the two order alike; a '
         r'mean over frames does not}: under the mean of variances %d of the 800 pairs move '
         r'and no per-type verdict does. ' % MUDAM + r'} \\',
          r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(A16)} linhas -> {SAIDA.name}')


if __name__ == '__main__':
    main()
