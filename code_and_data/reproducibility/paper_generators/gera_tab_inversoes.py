#!/usr/bin/env python3
"""A TABELA DAS INVERSOES: quais tipos cada operacao inverte, e com que significancia.

POR QUE EXISTE (08/09/2026). O corpo passou a afirmar que TODAS as celulas operacao-tipo
abaixo do acaso sao significativas sob Holm nos 120 testes. Uma afirmacao dessas precisa ser
conferivel sem rodar nada: aqui estao as celulas, uma a uma, com a acuracia e o p ajustado.

⚠️ A convencao de empate e a da Tabela 3 do corpo, que TIRA empate do denominador. A analise
de sensibilidade com o empate DENTRO devolve os mesmos vereditos, e isso vai na legenda.
"""
import os
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_inversoes.tex'

NOME = {
    'ke_edge_distribution': 'Edge distribution', 'ke_hue_count': "Hue count (Ke)",
    'ke_contraste': 'Contrast (Ke)', 'ke_colorfulness': 'Colourfulness (Ke)',
    'hasler_colorfulness': 'Colourfulness (Hasler)', 'laplacian_var': 'Laplacian variance',
    'contraste_variancia': 'Grey-level dispersion', 'glcm_contraste': 'GLCM contrast',
    'huang_saturacao': 'Saturation', 'qaroush_entropia': 'Entropy',
    'qaroush_gm': 'Gradient magnitude', 'qaroush_go': 'Gradient orientation',
    'qaroush_saliencia': 'Saliency area', 'srinivas_quality': 'Srinivas composite',
    'gygli_media_crua': 'Gygli mean of three',
}
TIPO = {'dark': 'Dk', 'motion': 'Mo', 'blur': 'Bl', 'h264': 'H2', 'rescale': 'Rs',
        'satur': 'St', 'noise': 'Ns', 'jpeg': 'Jp'}


def main():
    d = json.loads((QB / 'quantas_invertem_ALEM_DO_ACASO.json').read_text(encoding='utf-8'))
    # ⭐ 13/09: os empates existem e sao desiguais entre operacoes; com o empate no
    # denominador, «abaixo de 50» nao implica por si preferencia pelo degradado.
    _emp = d['empates_por_operacao']
    EMP_N = sum(1 for v in _emp.values() if v)
    EMP_MAX = max(_emp.values())
    EMP_QUEM = max(_emp, key=_emp.get).replace('_', r'\_')
    blo = json.loads((QB / 'o_binomial_respeita_o_bloco.json').read_text(encoding='utf-8'))
    perdem = set(blo['perdem_a_significancia_no_bloco'])
    # ⭐ 21/09: a terceira unidade, pedida pelo parecer externo (M44/E22/TB04). A tabela
    # marca as DUAS quedas, senao ela mostra um veredito unico onde ha uma escada.
    top = json.loads((QB / 'o_bloco_de_topico_e_a_unidade_mais_alta.json').read_text(encoding='utf-8'))
    perdem_top = set(top['perdem_do_segmento_para_o_topico'])
    _m = json.loads((QB / 'a_manchete_depende_de_quais_tipos.json').read_text(encoding='utf-8'))
    mtip, mseg = _m['por_cenario'], _m['tirando_um_segmento']
    ops = d['por_operacao']
    linhas = []
    for o, v in sorted(ops.items(), key=lambda x: (-len(x[1]['tipos_abaixo_de_50']),
                                                   x[1]['menor_acuracia'])):
        abaixo = v['tipos_abaixo_de_50']
        sig = set(v['tipos_significativos'])
        # ⚠️ se alguma celula abaixo do acaso NAO for significativa, ela sai marcada, e a
        # frase do corpo cai junto: a tabela nao pode esconder a excecao.
        # ⚠️ a daga agora marca a celula que NAO sobrevive ao teste na unidade declarada
        def _marca(t):
            k = '%s|%s' % (o, t)
            if k in perdem:
                return r'$^{\dagger}$'          # ja cai na unidade de segmento
            if k in perdem_top:
                return r'$^{\ddagger}$'         # sobrevive ao segmento, cai no topico
            return ''
        celulas = ', '.join(
            '%s~%.1f%s' % (TIPO[t], v['acuracia_por_tipo'][t], _marca(t)) for t in abaixo)
        cor = r'\rowcolor{rowlight}' if len(linhas) % 2 else ''
        pior = (r'\textcolor{accentred}{\textbf{%.1f}}' % v['menor_acuracia']
                if v['menor_acuracia'] < 25 else '%.1f' % v['menor_acuracia'])
        linhas.append(r'%s%s & %d & %s & %s \\' % (cor, NOME.get(o, o), len(abaixo),
                                                   pior, celulas))
    sens = d['sensibilidade_a_convencao_de_empate']
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        # ⭐ 22/09 (parecer v4, 2.2): a legenda dizia «the accuracy of each» sem dizer
        # QUAL. Esta tabela usa a DECISIVA e o corpo usa a ESTRITA; sem o denominador
        # escrito, as duas parecem discordar (Hue count no escurecimento: 20 e 21,7).
        '\\caption{Every operation--type cell below the 50 per cent chance floor, with its '
        '\\emph{decisive} accuracy $W/(W+L)$, which leaves ties out of the denominator and '
        'therefore differs from the strict accuracy of the main tables wherever an operation '
        'ties. Significance is an exact sign-flip randomization with Holm across '
        'the %d operation--type tests, reported for both nested units. Over the 20 '
        'broadcast segments, %d of the %d cells survive and $^{\\dagger}$ marks the '
        '%d that do not; over the %d topic blocks, the more conservative unit, %d survive '
        'and $^{\\ddagger}$ marks the further %d that fall. The %d cells in which an '
        'operation is wrong on all one hundred pairs carry neither mark: they survive in '
        'both units. Counting ties inside the denominator instead of outside '
        'leaves the same %d cells and the same %d operations. Removing the two types aligned '
        'with an operation\'s own attribute, darkening and desaturation, leaves all %d '
        'operations still inverting; removing white noise instead leaves %d. Dropping one '
        'segment at a time, all %d keep inverting in every one of the %d rounds. '
        '\\textbf{Ties are unevenly spread}: %d operations tie on at least one pair and the '
        'largest count is %d. Where ties are many, accuracy below 50 per cent does not by '
        'itself mean the degraded copy is preferred; the reading that does is correct '
        'against incorrect, which is what the sign-flip test compares. '
        'Dk = darkening, Mo = motion '
        'blur, Bl = Gaussian blur, H2 = H.264, Rs = rescaling, St = desaturation, '
        'Ns = white noise, Jp = JPEG.}\n'
        % (d['n_testes'], blo['significativas_sob_o_bloco_de_segmento'],
           sum(len(v['tipos_abaixo_de_50']) for v in ops.values()), len(perdem),
           top['n_blocos_principal'], top['significativas_sob_o_bloco_de_topico_12'],
           len(perdem_top), top['celulas_perfeitas_0_de_100'],
           sens['celulas_abaixo_de_50'], sens['operacoes_com_tipo_significativo'],
           mtip['sem os dois tipos alinhados']['invertem'], mtip['sem o ruido branco']['invertem'],
           len(ops), mseg['n_rodadas'], EMP_N, EMP_MAX) +
        '\\label{tab:inversoes}\n\\footnotesize\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{3.4cm}cc'
        '>{\\raggedright\\arraybackslash}p{5.6cm}@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Operation} & \\hd{Types} & \\hd{Worst} & \\hd{Cells below chance (\\%)} \\\\\n'
        '\\midrule\n' + '\n'.join(linhas) +
        '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  %d operacoes -> %s' % (len(linhas), SAIDA.name))


if __name__ == '__main__':
    main()
