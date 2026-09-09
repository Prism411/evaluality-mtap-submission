#!/usr/bin/env python3
"""A TABELA DOS DEZENOVE COMPOSTOS PUBLICADOS.

POR QUE EXISTE (08/09/2026). O corpo afirma que dezenove combinacoes de atributos foram
coletadas da literatura e que UMA passa a porta de sensibilidade e depois falha na
transferencia. ⛔ Mas o leitor nao tinha onde ver QUAIS sao as dezenove: a afirmacao mais
verificavel da secao era a menos auditavel.

⚠️ Estas combinacoes nao sao um ensemble montado por nos: sao os conjuntos de termos que os
PDFs do acervo de fato juntam, com a contagem de artigos que os usam.
"""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_compostos.tex'

NOME = {
    'qaroush_saliencia': 'saliency', 'spatial_information': 'spatial information',
    'lbp_uniformidade': 'LBP uniformity', 'hasler_colorfulness': 'colourfulness',
    'laplacian_var': 'Laplacian variance', 'ke_edge_distribution': 'edge distribution',
    'ke_contraste': 'contrast', 'ke_hue_count': 'hue count', 'ke_brightness': 'brightness',
    'ke_colorfulness': 'colourfulness (Ke)', 'contraste_variancia': 'contrast variance',
    'glcm_contraste': 'GLCM contrast', 'huang_saturacao': 'saturation',
    'qaroush_entropia': 'entropy', 'qaroush_gm': 'gradient magnitude',
    'qaroush_go': 'gradient orientation', 'sobel_cv': 'Sobel variation',
    'qaroush_ses': 'SES', 'qaroush_movimento': 'motion', 'qaroush_ct': 'CT',
    'huang_exposicao': 'exposure', 'huang_matiz': 'hue', 'brilho': 'brightness',
    'si': 'spatial information',
}


def rot(campos):
    return ' + '.join(NOME.get(c, c.replace('_', r'\_')) for c in campos)


def main():
    d = json.loads((QB / 'as_combinacoes_COMO_A_LITERATURA_PUBLICA.json').read_text(encoding='utf-8'))
    linhas = sorted(d['por_combinacao'], key=lambda x: (-x['media_z']['mean_rho'], -x['n_artigos']))
    out, passam = [], 0
    for c in linhas:
        z, g = c['media_z'], c['generalizacao_koniq_AJUSTADA']
        sens_ok = z['passa']
        passam += int(bool(sens_ok))
        sens = r'\textcolor{accentgreen}{\textbf{%.3f}}' % z['mean_rho'] if sens_ok \
            else '%.3f' % z['mean_rho']
        out.append(r'%s & %d & %s & %d & %s & %s \\'
                   % (rot(c['campos']), c['n_artigos'], sens.replace('0.', '.'),
                      z['tipos_acima_de_0_5'], ('%.3f' % g['rho_alinhado']).replace('0.', '.'),
                      'yes' if c['elegivel_pelas_duas_portas_mensuraveis'] else 'no'))
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{The %d attribute combinations the summarization literature publishes, with '
        'the number of archive papers that use each. These are not ensembles assembled here: '
        'each row is a set of terms some published work combines. \\emph{Sens.} is the '
        'within-reference mean on KADID-10k under the $z$-score aggregation and \\emph{Types} '
        'the count above $.50$ of 25; \\emph{Gen.} is the direction-aligned correlation on '
        'KonIQ-10k. \\textbf{%d of the %d clears the sensitivity gate} (green) and none is '
        'eligible, because that one does not transfer.}\n'
        % (len(linhas), passam, len(linhas)) +
        '\\label{tab:compostos}\n\\footnotesize\n\\setlength{\\tabcolsep}{4pt}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{6.0cm}ccccc@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Combination} & \\hd{Papers} & \\hd{Sens.} & \\hd{Types} & \\hd{Gen.} & '
        '\\hd{Eligible} \\\\\n\\midrule\n' + '\n'.join(out) +
        '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  %d compostos, %d passam a sensibilidade -> %s' % (len(linhas), passam, SAIDA.name))


if __name__ == '__main__':
    main()
