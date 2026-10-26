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
import re
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


# ⭐ 22/09 (parecer v7): o dagger era uma LISTA DIGITADA aqui dentro, e a legenda dizia
# «verificado contra a fonte com um trecho registrado» sem dizer ONDE esse trecho esta.
# ⛔ Marcador sem registro localizavel nao e verificacao: e afirmacao. Agora o conjunto sai
# do proprio arquivo dos trechos, e a legenda o nomeia. Se um trecho sair do arquivo, o
# dagger some junto, em vez de continuar impresso sobre nada.
VALIDA = 'o_que_cada_fonte_valida.json'


def _verificadas():
    import json as _json
    d = _json.loads((QB / VALIDA).read_text(encoding='utf-8'))['por_fonte']
    v = {k for k, e in d.items() if (e.get('verbatim') or '').strip()}
    assert v, '⛔ nenhuma fonte com trecho literal em %s' % VALIDA
    return v


VERIFICADAS = _verificadas()


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
        VERIF = VERIFICADAS
        def _quebravel(k):
            # deixa o LaTeX quebrar antes do ano e depois dele
            return re.sub(r'(\d{4})', r'\\allowbreak \1\\allowbreak ', k)
        fontes = ', '.join(
            (r'\cite{%s}' % a.replace('.pdf', ''))
            + (r'$^{\dagger}$' if a.replace('.pdf', '') in VERIF else '')
            for a in sorted(c['artigos']))
        out.append(r'%s & %s & %s & %d & %s & %s & %s \\'
                   % (rot(c['campos']), fontes, sens.replace('0.', '.'),
                      z['tipos_acima_de_0_5'], ('%.3f' % g['rho_alinhado']).replace('0.', '.'),
                      ('%.3f' % gr['rho_alinhado']).replace('0.', '.'),
                      'yes' if c['elegivel_forma_crua'] else 'no'))
    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        # ⭐ 22/09 (parecer v5, 2.2): a coluna de fontes precisa dizer O QUE e um citekey.
        '\\caption{\\emph{Source works} lists the archive citekeys whose full text matches the terms of each combination. \\textbf{A dagger marks the works whose use was verified against the source with a recorded excerpt}, held in \\texttt{' + VALIDA.replace('_', r'\_') + '} of the reproducibility package; the others are retrieval matches and are not evidence that the work adopts that combination, so the rows without a dagger are evaluated here as diagnostic configurations rather than as published algorithms. '
        'Screening of %d diagnostic configurations built from attributes identified in the '
        'archive; \\textbf{the aggregations are defined in this study}, not taken from a '
        'published algorithm. '
        # ⭐ 22/09 (parecer v7): «LBP» aparecia seis vezes na coluna e em lugar nenhum do
        # artigo por extenso.
        '\\emph{LBP} is the local binary pattern. '
        '\\emph{Sens.} is the within-reference mean against the degradation level on '
        'KADID-10k under the $z$-score aggregation and \\emph{Types} the count above $.50$ '
        'of 25. \\emph{Gen.}\\,($z$) is the direction-aligned correlation on KonIQ-10k as a '
        'magnitude, in the same configuration as \\emph{Sens.}; \\emph{Gen.}\\,(ridge) is the '
        'generous variant, fitted outside the reference and reported separately. '
        '\\textbf{Orientation comes from the data}, under the polarity-permissive rule of '
        'Section~3.3 of the main text, so a single-attribute row carries the opposite sign '
        'to Table~\\ref{tab:literature} exactly when the declared direction contradicts the '
        'data. Eligibility uses the $z$-score configuration throughout; green marks the '
        '%d row that clears the sensitivity gate.}\n'
        % (len(linhas), passam) +
        '\\label{tab:compostos}\n\\footnotesize\n\\setlength{\\tabcolsep}{3pt}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{2.7cm}>{\\raggedright\\arraybackslash}p{3.55cm}ccccc@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Combination} & \\hd{Source works} & \\hd{Sens.} & \\hd{Types} & '
        '\\hd{Gen. ($z$)} & \\hd{Gen. (ridge)} & '
        '\\hd{Eligible} \\\\\n\\midrule\n' + '\n'.join(out) +
        '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  %d compostos, %d passam a sensibilidade -> %s' % (len(linhas), passam, SAIDA.name))


if __name__ == '__main__':
    main()
