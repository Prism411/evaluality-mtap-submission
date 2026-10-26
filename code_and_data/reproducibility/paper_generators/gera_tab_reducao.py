#!/usr/bin/env python3
"""A REDUCAO: trocar o escore pela contagem muda alguma escolha?

POR QUE EXISTE (25/09/2026). O corpo mostra que o canal de contagem domina, e o
suplementar dizia que quem reintroduz a variacao de contagem e o SELETOR DE QUADROS-CHAVE,
variando quantos quadros retem. ⛔ O dado nao sustenta isso: o numero de quadros retidos
correlaciona +0,177 com o escore (p 0,11) e reproduz 23 de 42 escolhas, que e quase moeda.
Quem reproduz o escore e a CONTAGEM DE DESCRITORES, e ela e carregada pelo detalhe POR
QUADRO (+0,599), nao pelo numero de quadros.

⭐ A tabela faz a substituicao direta, que e o teste mais duro possivel do mecanismo:
troque o escore por cada quantidade e veja quantas das 42 escolhas continuam as mesmas.

Fonte: `a_reducao_no_regime_implantado.json`, no regime implantado — o `n_desc` vem dos
quadros-chave que o pipeline seleciona, nao dos dez quadros casados.
"""
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_reducao.tex'
FONTE = 'a_reducao_no_regime_implantado.json'

NOME = {
    'n_desc': ('Descriptor count', r'the number of SIFT descriptors the key frames yield'),
    'kp_density': ('Keypoints per frame', r'descriptor count divided by frames retained'),
    'n_frames': ('Frames retained', r'how many key frames the selector keeps'),
    'bovw_per_frame': ('Score per frame', r'the score divided by frames retained'),
    'bovw_per_desc': ('Score per descriptor', r'the mean rarity weight of Eq.~3 of the main article'),
}
ORDEM = ['n_desc', 'kp_density', 'n_frames', 'bovw_per_frame', 'bovw_per_desc']


def main():
    d = json.loads((QB / FONTE).read_text(encoding='utf-8'))
    sub, cor = d['\u2b50_por_quantidade_substituta'], d['correlacao_com_o_score_publicado']
    n_cl, n_seg = d['n_clusters'], d['n_segmentos_distintos']
    assert n_cl == 42, n_cl

    linhas = []
    for i, k in enumerate(ORDEM):
        c = cor[k]
        rho = ('%+.3f' % c['spearman_com_bovw_sum']).replace('0.', '.')
        # ⚠️ o p entra so quando NAO separa: e ele que torna o resultado negativo legivel
        p = c['p']
        marca = '' if p < .01 else (r'$^{\ast}$' if p < .05 else r'$^{\mathrm{ns}}$')
        s = sub.get(k)
        esc = (r'%d\,/\,%d' % (s['escolhas_iguais'], s['de_clusters'])) if s else '---'
        par = (r'%d\,/\,%d' % (s['pares_na_mesma_ordem'], s['de_pares'])) if s else '---'
        linhas.append(r'\rowcolor{%s}%s & %s & $%s$%s & %s & %s \\'
                      % ('rowlight' if i % 2 else 'rowwhite', NOME[k][0], NOME[k][1],
                         rho, marca, esc, par))

    dur = d['\u26a0\ufe0f_a_duracao_pergunta_5_da_critica_10']
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{Replacing the score by a simpler quantity, on the %d application '
        'clusters and %d distinct segments. \\emph{$\\rho$} is the Spearman correlation '
        'with the published score; \\emph{Same choice} counts the clusters whose selected '
        'representative is unchanged when the quantity replaces the score, and '
        '\\emph{Same order} the ordered pairs it preserves. \\textbf{The descriptor count '
        'reproduces every choice}, so the operation is that count. \\textbf{How many key '
        'frames the selector retains does not}: it tracks the score at $%s$ and reproduces '
        'barely more than half the choices, while keypoints per frame tracks it at $%s$. '
        'The count is therefore carried by detail per frame rather than by the number of '
        'frames. Segment duration ranges from %.1f to %.1f seconds and does not predict '
        'the score ($\\rho=%s$) or the count ($\\rho=%s$). Marks: $^{\\ast}$ $p<.05$, '
        '$^{\\mathrm{ns}}$ not significant; all other rows have $p<.01$.}\n'
        % (n_cl, n_seg,
           ('%+.3f' % cor['n_frames']['spearman_com_bovw_sum']).replace('0.', '.'),
           ('%+.3f' % cor['kp_density']['spearman_com_bovw_sum']).replace('0.', '.'),
           dur['duracao_s']['min'], dur['duracao_s']['max'],
           ('%+.3f' % dur['spearman_duracao_x_bovw_sum']).replace('0.', '.'),
           ('%+.3f' % dur['spearman_duracao_x_n_desc']).replace('0.', '.')) +
        '\\label{tab:reducao}\n\\footnotesize\n\\setlength{\\tabcolsep}{4pt}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{2.9cm}'
        '>{\\raggedright\\arraybackslash}p{4.6cm}ccc@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Quantity} & \\hd{What it is} & \\hd{$\\rho$} & \\hd{Same choice} & '
        '\\hd{Same order} \\\\\n\\midrule\n' + '\n'.join(linhas) +
        '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  %d quantidades -> %s' % (len(ORDEM), SAIDA.name))


if __name__ == '__main__':
    main()
