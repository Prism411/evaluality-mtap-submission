#!/usr/bin/env python3
"""A TABELA DOS DEZENOVE COMPOSTOS PUBLICADOS.

POR QUE EXISTE (08/09/2026). O corpo afirma que dezenove combinacoes de atributos foram
coletadas da literatura e que UMA passa a porta de sensibilidade e depois falha na
transferencia. ⛔ Mas o leitor nao tinha onde ver QUAIS sao as dezenove: a afirmacao mais
verificavel da secao era a menos auditavel.

⚠️ Estas combinacoes nao sao um ensemble montado por nos: sao os conjuntos de termos que os
PDFs do acervo de fato juntam, com a contagem de artigos que os usam.
"""
import os
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
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
        z, g = c['media_z'], c['generalizacao_koniq']          # a MESMA forma nas duas
        gr = c['generalizacao_koniq_AJUSTADA']                  # o ridge, em coluna propria
        sens_ok = z['passa']
        passam += int(bool(sens_ok))
        sens = r'\textcolor{accentgreen}{\textbf{%.3f}}' % z['mean_rho'] if sens_ok \
            else '%.3f' % z['mean_rho']
        out.append(r'%s & %d & %s & %d & %s & %s & %s \\'
                   % (rot(c['campos']), c['n_artigos'], sens.replace('0.', '.'),
                      z['tipos_acima_de_0_5'], ('%.3f' % g['rho_alinhado']).replace('0.', '.'),
                      ('%.3f' % gr['rho_alinhado']).replace('0.', '.'),
                      'yes' if c['elegivel_forma_crua'] else 'no'))
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{The %d attribute combinations the summarization literature publishes, with '
        'the number of archive papers that use each. These are not ensembles assembled here: '
        'each row is a set of terms some published work combines. \\emph{Sens.} is the '
        'within-reference mean against the degradation level on KADID-10k under the '
        '$z$-score aggregation. \\textbf{Orientation here comes from the data}, the sign of '
        'the mean across types, because a combination of attributes has no direction declared '
        'by any source, whereas Table~S18 orients each operation by the direction its own '
        'source states. Magnitudes match across the two tables; a single-attribute row '
        'therefore carries the opposite sign to Table~S18 exactly when the declared direction '
        'contradicts the data. \\textbf{This makes the gate here the more permissive of the '
        'two}, since $|\\rho|\\ge\\rho^{*}$, so the verdict below is conservative: no '
        'composite clears it even under the looser orientation. \\emph{Types} is '
        'the count above $.50$ of 25; \\emph{Gen.} is the direction-aligned correlation on '
        'KonIQ-10k as a magnitude, under the same orientation rule as the sensitivity column. '
        '\\textbf{Sensitivity and Gen.\\,($z$) are the same configuration}; the ridge '
        'column is the generous variant, fitted outside the reference and reported '
        'separately rather than mixed into the verdict. \\textbf{Eligibility below uses '
        'the $z$-score configuration throughout}, and the count is the same under either '
        'consistent choice: zero of the %d are eligible whether both gates use the $z$ '
        'form or both use the ridge form. \\textbf{%d of the %d clears the sensitivity gate} (green) and none is '
        'eligible, because that one does not transfer.}\n'
        % (len(linhas), len(linhas), passam, len(linhas)) +
        '\\label{tab:compostos}\n\\footnotesize\n\\setlength{\\tabcolsep}{3pt}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{4.9cm}cccccc@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Combination} & \\hd{Papers} & \\hd{Sens.} & \\hd{Types} & '
        '\\hd{Gen. ($z$)} & \\hd{Gen. (ridge)} & '
        '\\hd{Eligible} \\\\\n\\midrule\n' + '\n'.join(out) +
        '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  %d compostos, %d passam a sensibilidade -> %s' % (len(linhas), passam, SAIDA.name))


if __name__ == '__main__':
    main()
