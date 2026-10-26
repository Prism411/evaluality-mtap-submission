#!/usr/bin/env python3
"""A TABELA DAS UNIDADES DE INFERENCIA: em que unidade cada intervalo foi reamostrado.

POR QUE EXISTE (08/09/2026). O corpo declarava «segment-block 95 % CI» num intervalo que
reproduzia pela reamostragem POR PAR, e nada no artigo ligava o rotulo ao numero. Corrigido
o caso, ficou a classe: cada bloco de evidencia declara uma unidade, e o leitor nao tinha
onde conferir qual. Esta tabela poe as quatro lado a lado, com a unidade RIVAL que foi
testada — porque exigir so que a declarada reproduza nao separa nada: duas unidades que
acertem as duas nao dizem qual foi usada.

Fonte: `as_quatro_unidades_declaradas.json`, do benchmark.
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

# ⭐ 14/09: o parecer pediu o intervalo por TOPICO da diferenca pareada. Ele ja estava
# medido em `as_tres_unidades`, ao lado do por segmento e do por par; faltava sair do
# arquivo. Os 800 pares vem de 20 segmentos e os 20 segmentos de 13 topicos, entao ha
# DUAS unidades mais grossas que o par, e a linha passa a mostrar as duas.
TRES = 'o_bloco_de_segmento_reproduz_um_intervalo_publicado.json'
FUSAO = 'a_fusao_de_fontes_vale_na_aplicacao.json'


def _faixa(par):
    """`[a, b]` em LaTeX, com o zero a esquerda cortado como no resto da tabela."""
    return r'$[%s, %s]$' % tuple(('%.1f' % x) for x in par)


def concreto(k, e):
    """A propriedade que sustenta o veredito, em vez do proprio veredito.

    ⛔ Nada aqui e digitado: ou sai do campo `quantos`, que conta limites, ou das duas
    dispersoes por semente. Se um eixo perder as duas formas, a funcao ESTOURA em vez de
    devolver a frase generica de volta.
    """
    import re
    if e.get('quantos'):
        m = re.match(r'(\d+) de (\d+).*?sob a declarada, (\d+) de (\d+) sob a rival',
                     e['quantos'])
        assert m, '⛔ `quantos` mudou de forma em %r: %r' % (k, e['quantos'])
        a, n, b, n2 = (int(x) for x in m.groups())
        assert n == n2, '⛔ denominadores diferentes em %r: %s' % (k, e['quantos'])
        return ('%d of the %d interval bounds reproduce under the declared unit, %d '
                'under the rival' % (a, n, b))
    if 'dispersao_em_8_sementes_topico' in e:
        top, clu = e['dispersao_em_8_sementes_topico'], e['dispersao_em_8_sementes_cluster']
        return ('over eight seeds the bounds span %s and %s under the declared unit, '
                'against %s and %s under the rival'
                % (_faixa(top[0]), _faixa(top[1]), _faixa(clu[0]), _faixa(clu[1])))
    raise AssertionError('⛔ %r nao traz nem `quantos` nem dispersao por semente' % k)


def main():
    d = json.loads((QB / 'as_quatro_unidades_declaradas.json').read_text(encoding='utf-8'))
    # ⛔ o aninhamento e MEDIDO, nao digitado: 13 topicos atras dos 20 segmentos, e nao 11,
    # que era o numero de limites conferidos e quase virou numero de topicos na tabela.
    u = json.loads((QB / 'a_unidade_declarada_e_a_que_reproduz.json').read_text(encoding='utf-8'))
    assert u['n_segmentos'] == 20 and u['n_topicos'] == 13, u
    # ⛔ 22/09 (parecer v7, 2.1): a tabela dizia «13 news topics» numa linha e «(12
    # topics)» na de cima, e as duas estavam certas — 13 ROTULOS, 12 BLOCOS depois de
    # fundir os dois que partilham os .mp4. Dois numeros vizinhos para a mesma palavra e
    # o defeito, nao o valor. Agora cada linha diz os dois, e os dois saem de arquivo.
    tres = json.loads((QB / TRES).read_text(encoding='utf-8'))['manchete']['as_tres_unidades']
    n_rot = tres['bloco_de_rotulo_13_sem_fundir']['n_blocos']
    n_blo = tres['bloco_de_topico']['n_blocos']
    assert n_rot == u['n_topicos'] and n_blo < n_rot, \
        '⛔ os dois arquivos discordam no numero de rotulos: %s x %s' % (n_rot, u['n_topicos'])
    fus = json.loads((QB / FUSAO).read_text(encoding='utf-8'))['por_linha']['liqe_x_implantada']
    for k in ('acuracia estrita, 800 pares (S19)',):
        EIXO[k] = EIXO[k][:4] + (
            'the %d segments come from %d topic labels, %d source-aware blocks after '
            'merging the two that share source videos' % (u['n_segmentos'], n_rot, n_blo),)
    for k in ('piso in-domain, 42 clusters', 'contraste de saida, 42 clusters'):
        EIXO[k] = EIXO[k][:4] + (
            'the 42 clusters come from %d topic labels, %d source-aware blocks'
            % (fus['sem_fundir']['n_blocos'], fus['fundido']['n_blocos']),)
    linhas = []
    for k in ORDEM:
        e = d['por_eixo'][k]
        nome, bloco, decl, rival, nest = EIXO[k]
        corrigido = e['veredito'].startswith('⛔')
        cor = 'perf3!45' if corrigido else 'perf5!25'
        if corrigido:
            veredito = (r'\textbf{the two units give different widths; under the declared '
                        r'unit the interval is $[+%.1f,+%.1f]$}' % tuple(e['publicado_agora']))
            if k == 'diferenca pareada, 800 pares':
                tres = json.loads((QB / TRES).read_text(encoding='utf-8'))['manchete']['as_tres_unidades']
                seg, top = tres['bloco_de_segmento'], tres['bloco_de_topico']
                # ⛔ os dois arquivos tem de concordar no segmento, senao um deles esta velho
                assert [round(x, 1) for x in seg['ic_impresso']] == \
                       [round(x, 1) for x in e['publicado_agora']], \
                    '⛔ o IC por segmento difere entre os dois arquivos: %s x %s' % (
                        seg['ic_impresso'], e['publicado_agora'])
                veredito += (r', and $[%s, %s]$ under the coarser source-aware block '
                             r'(%d blocks)'
                             % (top['imprime'][0], top['imprime'][1], top['n_blocos']))
        else:
            # ⭐ 22/09 (parecer v7): «reproduz sob a declarada e nao sob a rival» era o
            # ROTULO da coluna dito outra vez. Aqui vai a propriedade concreta que
            # produziu esse rotulo, lida do arquivo: quantos limites reproduzem, ou as
            # duas dispersoes por semente quando o eixo nao conta limites.
            veredito = concreto(k, e)
        linhas.append(
            r'\rowcolor{%s}%s & %s & %s & %s & %s \\' %
            (cor, bloco, nome, decl, rival, veredito))
        linhas.append(r'\rowcolor{%s} & \multicolumn{4}{@{}>{\raggedright\arraybackslash\itshape}p{9.55cm}@{}}{\footnotesize %s} \\'
                      % (cor, nest))
        linhas.append(r'\cmidrule(lr){1-5}')

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
        r'\rowcolor{%s} & \multicolumn{4}{@{}>{\raggedright\arraybackslash\itshape}p{9.55cm}@{}}{\footnotesize the %d discordant '
        r'pairs fall in %d topics; the null enumerates all $2^{%d}$ block sign '
        r'assignments} \\' %
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
        'same block. Each interval is also recomputed under the rival unit, and the last '
        'column reports the outcome of that recomputation.}\n'
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
