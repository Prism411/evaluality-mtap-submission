#!/usr/bin/env python3
"""A TABELA DAS UNIDADES DE INFERENCIA: em que unidade cada intervalo foi reamostrado.

POR QUE EXISTE (08/09/2026). O corpo declarava «segment-block 95 % CI» num intervalo que
reproduzia pela reamostragem POR PAR, e nada no artigo ligava o rotulo ao numero. Corrigido
o caso, ficou a classe: cada bloco de evidencia declara uma unidade, e o leitor nao tinha
onde conferir qual. Esta tabela poe as quatro lado a lado, com a unidade RIVAL que foi
testada — porque exigir so que a declarada reproduza nao separa nada: duas unidades que
acertem as duas nao dizem qual foi usada.

Fonte: `as_quatro_unidades_declaradas.json`, do quality-benchmark.
"""
import os
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_unidades.tex'

# a leitura em ingles de cada eixo, e o bloco de evidencia a que ele pertence
EIXO = {
    'diferenca pareada, 800 pares': (
        'Paired difference, 800 pairs', 'Block 01', 'segment block',
        'the pair', r'20 segments, 40 pairs each; pairs within a segment share content'),
    'acuracia estrita, 800 pares (S19)': (
        'Strict accuracy, 800 pairs', 'Block 01', 'topic block',
        'the segment block', r'the 20 segments come from 13 news topics'),
    'piso in-domain, 42 clusters': (
        'In-domain floor, 42 clusters', 'Block 04', 'topic block',
        'the cluster', r'the 42 clusters come from 19 topics'),
    'contraste de saida, 42 clusters': (
        'Output contrast, 42 clusters', 'Block 04', 'topic block',
        'the cluster', r'the 42 clusters come from 19 topics'),
}
ORDEM = ['diferenca pareada, 800 pares', 'acuracia estrita, 800 pares (S19)',
         'piso in-domain, 42 clusters', 'contraste de saida, 42 clusters']

# ⭐ 12/09: o quinto eixo nao estava na varredura de 08/09 porque ele nao declarava unidade
# nenhuma — usava McNemar, que supoe independencia entre os 42 clusters. Entra aqui com o
# mesmo tratamento dos outros quatro: recomputado sob a unidade que o desenho implica, com
# o esquema anterior como rival.
MCNEMAR = 'o_mcnemar_dos_42_com_topico_como_unidade.json'


def main():
    d = json.loads((QB / 'as_quatro_unidades_declaradas.json').read_text(encoding='utf-8'))
    # ⛔ o aninhamento e MEDIDO, nao digitado: 13 topicos atras dos 20 segmentos, e nao 11,
    # que era o numero de limites conferidos e quase virou numero de topicos na tabela.
    u = json.loads((QB / 'a_unidade_declarada_e_a_que_reproduz.json').read_text(encoding='utf-8'))
    assert u['n_segmentos'] == 20 and u['n_topicos'] == 13, u
    for k in ('acuracia estrita, 800 pares (S19)',):
        EIXO[k] = EIXO[k][:4] + ('the %d segments come from %d news topics'
                                 % (u['n_segmentos'], u['n_topicos']),)
    linhas = []
    for k in ORDEM:
        e = d['por_eixo'][k]
        nome, bloco, decl, rival, nest = EIXO[k]
        corrigido = e['veredito'].startswith('⛔')
        cor = 'perf3!45' if corrigido else 'perf5!25'
        if corrigido:
            veredito = (r'\textbf{the published interval matched the rival scheme; '
                        r'corrected to $[+%.1f,+%.1f]$}' % tuple(e['publicado_agora']))
        else:
            veredito = 'reproduces under the declared unit and not under the rival'
        linhas.append(
            r'\rowcolor{%s}%s & %s & %s & %s & %s \\' %
            (cor, bloco, nome, decl, rival, veredito))
        linhas.append(r'\rowcolor{%s} & \multicolumn{4}{@{}l@{}}{\footnotesize\emph{%s}} \\'
                      % (cor, nest))

    # ⭐ o quinto eixo: o contraste que usava McNemar, refeito em bloco de topico
    m = json.loads((QB / MCNEMAR).read_text(encoding='utf-8'))
    assert m['pre_condicao_reproduz_o_publicado']['reproduz'], \
        '⛔ o McNemar em bloco nao reproduziu o publicado: nao entra na tabela'
    b = m['COM_O_TOPICO_COMO_UNIDADE']
    cor = 'perf5!25' if b['separa_a_005'] else 'perf3!45'
    linhas.append(
        r'\rowcolor{%s}Block 04 & Regime contrast, 42 clusters & topic block & '
        r'the cluster (exact McNemar) & the verdict holds under the declared unit '
        r'($p=%s$ against $p=%s$) \\' %
        (cor, ('%.3f' % b['p_troca_de_sinal_em_bloco']).lstrip('0'),
         ('%.3f' % m['pre_condicao_reproduz_o_publicado']['p_mcnemar_exato']).lstrip('0')))
    linhas.append(
        r'\rowcolor{%s} & \multicolumn{4}{@{}l@{}}{\footnotesize\emph{the %d discordant '
        r'pairs fall in %d topics; the null enumerates all $2^{%d}$ block sign '
        r'assignments}} \\' %
        (cor, m['pre_condicao_reproduz_o_publicado']['n10']
         + m['pre_condicao_reproduz_o_publicado']['n01'],
         b['topicos_que_carregam_discordante'], b['topicos_que_carregam_discordante']))
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{Resampling unit per analysis, and the rival unit tested against it. '
        'Observations are nested, so the unit decides the width of every interval: the '
        'italic line under each row states the nesting, and \\textbf{the declared unit '
        'follows from that nesting}, observations sharing content or a source entering the '
        'same block. Each interval was then recomputed under the rival unit; \\textbf{that '
        'check identifies which implementation produced a published bound}, and is reported '
        'as a verification rather than as the reason for the choice. One of the five did not pass '
        'and was corrected; the last row is the contrast that previously declared no unit '
        'at all.}\n'
        '\\label{tab:unidades}\n\\footnotesize\n\\setlength{\\tabcolsep}{4pt}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{1.0cm}'
        '>{\\raggedright\\arraybackslash}p{2.35cm}'
        '>{\\raggedright\\arraybackslash}p{1.6cm}'
        '>{\\raggedright\\arraybackslash}p{1.6cm}'
        '>{\\raggedright\\arraybackslash}p{4.1cm}@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Block} & \\hd{Analysis} & \\hd{Declared unit} & \\hd{Rival tested} & '
        '\\hd{Outcome} \\\\\n\\midrule\n' +
        '\n'.join(linhas) +
        '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  %d eixos -> %s' % (len(ORDEM) + 1, SAIDA.name))


if __name__ == '__main__':
    main()
