#!/usr/bin/env python3
"""Tabela do suplementar: expressoes publicadas contra a propriedade que elas nomeiam.

Duas fontes que especificam um MODULO completo tambem especificam, no mesmo paragrafo, uma
propriedade que a expressao dada nao tem. Nos dois casos a varredura e por construcao e nao
envolve corpus: e uma propriedade da formula."""
import os
import json
import re
from pathlib import Path


# ⛔ `` comia o zero INTERNO: 40.5 virava 4.5.
# Tira so o zero a esquerda do ponto que nao vem depois de digito.
def sem_zero(t):
    return re.sub(r'(?<![0-9])0\.', '.', t)


import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_ct.tex'
ROTULO = {
    'a_Eq8_com_modulo': (r'$\frac{1}{K}\sum_k\bigl|\sigma_p(\mathrm{HE}(f_k))-'
                         r'\sigma_p(f_k)\bigr|$', 'Eq.~8 as published'),
    'sem_o_modulo': (r'$\frac{1}{K}\sum_k\bigl(\sigma_p(\mathrm{HE}(f_k))-\sigma_p(f_k)\bigr)$',
                     'without the absolute value'),
    'razao_que_a_fonte_NAO_escreve': (r'$\frac{1}{K}\sum_k \sigma_p(f_k)/'
                                      r'\sigma_p(\mathrm{HE}(f_k))$',
                                      'ratio, unwritten in the source'),
}


def main():
    ct = json.load(open(QB / 'o_CT_do_qaroush_inverte_por_construcao.json'))
    br = json.load(open(QB / 'o_brilho_do_korolkov_premia_o_que_diz_penalizar.json'))
    r = ct['spearman_com_o_contraste_real']

    def num(v):
        t = sem_zero(f'${v:+.4f}$')
        return rf'\textcolor{{accentred}}{{\textbf{{{t}}}}}' if v < 0 else t

    L = [r'\begin{table}[!ht]', r'\centering',
         r'\caption{Two published expressions against the property the same paragraph '
         r'claims for them. \textbf{Above}: the contrast term of the Qaroush '
         r'visual-attention objective, over a sweep in which contrast rises by '
         rf'construction ({ct["n_niveis"]} levels, seed {ct["semente"]}). Histogram '
         r'equalisation raises the standard deviation of every frame in this sweep. Over '
         r'it, the published form and the form without the absolute value are both '
         r'perfectly inversely associated with the measure used to build the inputs; only '
         r'the ratio, which the equation does not write, is perfectly positively '
         r'associated. \textbf{Below}: the brightness term of the Korolkov module, '
         rf'over a sweep in which exposure rises by construction ({br["n_niveis"]} levels). '
         r"The source states that it ``penalizes under- and over-exposed frames'', which "
         r'requires a non-monotone function; the mean luminance it specifies is monotone '
         rf'and enters the module with weight ${br["peso_do_brilho_no_modulo"]:+.1f}$, so a '
         # ⛔ 22/09 (parecer v6, 2.3): as duas inversoes nao tem o mesmo estatuto. A do
         # Korolkov sai da expressao (termo monotono com peso positivo); a do Qaroush e o
         # comportamento MEDIDO nesta varredura, e generaliza-la exigiria controlar como o
         # desvio equalizado varia com o da entrada, o que nao esta estabelecido.
         r'brighter frame always scores higher. \textbf{No corpus is involved.} The '
         r'Korolkov inversion follows from the expression; the Qaroush result is the '
         r'behaviour of the expression over this sweep.}',
         # ⚠️ a primeira coluna era `l` e nao quebrava: o rotulo mais longo somado a
         # expressao em math passava 6,7 mm da margem. Agora ela quebra.
         r'\label{tab:ct}', r'\footnotesize', r'\setlength{\tabcolsep}{3.5pt}',
         r'\renewcommand{\arraystretch}{1.35}',
         r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{4.0cm} l r@{}}', r'\toprule', r'\rowcolor{headerblue}',
         r'\hd{Reading} & \hd{Expression} & \hd{$\rho$ with the property} \\',
         r'\midrule',
         r'\multicolumn{3}{@{}l}{\textit{Qaroush contrast, against contrast '
         r'(Eq.~8)}} \\']
    for i, (k, (expr, nome)) in enumerate(ROTULO.items()):
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        L.append(f'{cor}\\quad {nome} & {expr} & {num(r[k])} \\\\')
    L += [r'\midrule',
          r'\multicolumn{3}{@{}l}{\textit{Korolkov brightness, against exposure}} \\',
          r'\quad as published & $\frac{1}{|I|}\sum_{x,y} L(I)_{x,y}$ (LAB) & '
          + num(br['spearman_publicado_com_exposicao']) + r' \\',
          r'\rowcolor{rowlight}\quad illustrative non-monotone penalty & '
          r'$-\bigl|L-127.5\bigr|$ & '
          + num(br['spearman_da_forma_que_cumpre_o_texto']) + r' \\',
          r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  2 expressoes, {len(ROTULO) + 2} linhas -> {SAIDA.name}')


if __name__ == '__main__':
    main()
