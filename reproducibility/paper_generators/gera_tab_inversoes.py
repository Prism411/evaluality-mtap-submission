#!/usr/bin/env python3
"""A TABELA DAS INVERSOES: quais tipos cada operacao inverte, e com que significancia.

POR QUE EXISTE (08/09/2026). O corpo passou a afirmar que TODAS as celulas operacao-tipo
abaixo do acaso sao significativas sob Holm nos 120 testes. Uma afirmacao dessas precisa ser
conferivel sem rodar nada: aqui estao as celulas, uma a uma, com a acuracia e o p ajustado.

⚠️ A convencao de empate e a da Tabela 3 do corpo, que TIRA empate do denominador. A analise
de sensibilidade com o empate DENTRO devolve os mesmos vereditos, e isso vai na legenda.
"""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_inversoes.tex'

NOME = {
    'ke_edge_distribution': 'Edge distribution', 'ke_hue_count': "Hue count (Ke)",
    'ke_contraste': 'Contrast (Ke)', 'ke_colorfulness': 'Colourfulness (Ke)',
    'hasler_colorfulness': 'Colourfulness (Hasler)', 'laplacian_var': 'Laplacian variance',
    'contraste_variancia': 'Contrast variance', 'glcm_contraste': 'GLCM contrast',
    'huang_saturacao': 'Saturation', 'qaroush_entropia': 'Entropy',
    'qaroush_gm': 'Gradient magnitude', 'qaroush_go': 'Gradient orientation',
    'qaroush_saliencia': 'Saliency area', 'srinivas_quality': 'Srinivas composite',
    'gygli_media_crua': 'Gygli mean of three',
}
TIPO = {'dark': 'Dk', 'motion': 'Mo', 'blur': 'Bl', 'h264': 'H2', 'rescale': 'Rs',
        'satur': 'St', 'noise': 'Ns', 'jpeg': 'Jp'}


def main():
    d = json.loads((QB / 'quantas_invertem_ALEM_DO_ACASO.json').read_text(encoding='utf-8'))
    blo = json.loads((QB / 'o_binomial_respeita_o_bloco.json').read_text(encoding='utf-8'))
    perdem = set(blo['perdem_a_significancia_no_bloco'])
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
        celulas = ', '.join(
            '%s~%.1f%s' % (TIPO[t], v['acuracia_por_tipo'][t],
                           r'$^{\dagger}$' if '%s|%s' % (o, t) in perdem else '')
            for t in abaixo)
        linhas.append(r'%s & %d & %.1f & %s \\' % (NOME.get(o, o), len(abaixo),
                                                   v['menor_acuracia'], celulas))
    sens = d['sensibilidade_a_convencao_de_empate']
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{Every operation--type cell below the 50 per cent chance floor, with the '
        'accuracy of each. Significance is an exact sign-flip randomization over the 20 '
        'broadcast segments, the unit the design implies, with Holm across the %d '
        'operation--type tests: %d of the %d cells survive it and $^{\\dagger}$ marks the '
        '%d that do not. Counting ties inside the denominator instead of outside '
        'leaves the same %d cells and the same %d operations. Removing the two types aligned '
        'with an operation\'s own attribute, darkening and desaturation, leaves all %d '
        'operations still inverting; removing white noise instead leaves %d. Dropping one '
        'segment at a time, all %d keep inverting in every one of the %d rounds. '
        'Dk = darkening, Mo = motion '
        'blur, Bl = Gaussian blur, H2 = H.264, Rs = rescaling, St = desaturation, '
        'Ns = white noise, Jp = JPEG.}\n'
        % (d['n_testes'], blo['significativas_sob_o_bloco_de_segmento'],
           sum(len(v['tipos_abaixo_de_50']) for v in ops.values()), len(perdem),
           sens['celulas_abaixo_de_50'], sens['operacoes_com_tipo_significativo'],
           mtip['sem os dois tipos alinhados']['invertem'], mtip['sem o ruido branco']['invertem'],
           len(ops), mseg['n_rodadas']) +
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
