#!/usr/bin/env python3
"""OS DEZESSETE DA COMPARACAO AUXILIAR, NA REGUA DA TABELA 6 E NA RIVAL.

POR QUE EXISTE (23/09/2026, parecer v8, §3). O corpo dizia «o suplementar registra os
dezessete com suas acuracias» e o revisor procurou esse registro e NAO O ACHOU.

🔴 REFEITA EM 25/09 (parecer v9, §1.1), e a primeira versao desta tabela estava ERRADA.
Ela lia a media do `TABELA_FINAL.json`, que e OUTRA AGREGACAO da MESMA medicao, e a
imprimia sob a legenda da Tabela 6. Duas escolhas nao canonicas de uma vez:
  1. acuracia DECISIVA (empate fora do denominador) onde a Tabela 6 declara ESTRITA;
  2. media com os tipos ALINHADOS POR CONSTRUCAO FORA, que sao outros em cada linha.
⛔ E um terceiro erro por cima: o IC que eu imprimia ao lado cerca a media COM exclusao,
nao a acuracia impressa; e a coluna «800 comparisons» era falsa nas linhas em que a
exclusao deixa 400. ⚠️ As duas escolhas se movem em SENTIDOS CONTRARIOS — empate sobe,
exclusao desce — e por isso a tabela saia ora acima ora abaixo da Tabela 6, que foi
exatamente o que o revisor notou ao dizer que empate nao explicava os casos menores.

⭐ A CANONICA e a da Tabela 6: ESTRITA, media sobre as OITO degradacoes. As acuracias
POR TIPO sao identicas nos dois arquivos — nao ha duas rodadas, ha duas agregacoes.
⭐ As duas vao lado a lado aqui, nomeadas, porque a rival tambem esta publicada noutros
lugares e o leitor precisa saber qual e qual.

Fonte: `os_dezessete_na_regua_da_tabela6.json`, cujo controle e reproduzir o `sobel_cv`
publicado celula a celula e a mediana 74,8 que as quinze medias da Tabela 6 produzem.
"""
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_dezessete.tex'

FONTE = 'os_dezessete_na_regua_da_tabela6.json'
POREXT = {1: 'one', 2: 'two', 3: 'three', 4: 'four'}
# as siglas sao as da Tabela 6, para as duas pecas nomearem o tipo do mesmo jeito
SIGLA = {'dark': 'Dk', 'motion': 'Mo', 'blur': 'Bl', 'h264': 'H2',
         'rescale': 'Rs', 'satur': 'St', 'noise': 'Ns', 'jpeg': 'Jp'}

NOME = {
    'qaroush_saliencia': 'Saliency', 'ke_hue_count': 'Hue count (Ke)',
    'qaroush_go': 'Gradient orientation', 'sobel_cv': 'Sobel variation coefficient',
    'huang_saturacao': 'Saturation', 'qaroush_movimento': 'Motion',
    'qaroush_entropia': 'Entropy', 'ke_edge_distribution': 'Edge distribution',
    'qaroush_gm': 'Gradient magnitude', 'gygli_media_crua': 'Averaged aesthetics (Gygli)',
    'laplacian_var': 'Laplacian variance', 'ke_contraste': 'Contrast (Ke)',
    'srinivas_quality': 'The mean rule (Srinivas)', 'contraste_variancia': 'Grey-level dispersion',
    'glcm_contraste': 'GLCM contrast', 'hasler_colorfulness': 'Colourfulness (Hasler)',
    'ke_colorfulness': 'Colourfulness (Ke)',
}


def main():
    d = json.loads((QB / FONTE).read_text(encoding='utf-8'))
    membros, dez, qui = d['membros'], d['dezessete'], d['quinze_do_inventario_direcional']
    extras = set(d['fora_do_inventario_direcional'])
    assert dez['n'] == 17 and qui['n'] == 15, (dez['n'], qui['n'])

    out = []
    for nome, m in sorted(membros.items(), key=lambda kv: kv[1]['media_estrita_oito']):
        marca = r'$^{\ddagger}$' if nome in extras else ''
        cor = 'rowlight' if len(out) % 2 else 'rowwhite'
        # ⛔ o denominador da rival e MEDIDO, nao suposto: ele cai onde ha tipo excluido
        fora = ', '.join(SIGLA[x] for x in m['rival_tipos_excluidos']) or '---'
        out.append(r'\rowcolor{%s}\texttt{%s}%s & %s & %.1f & %.1f & %s & %d \\'
                   % (cor, nome.replace('_', r'\_\allowbreak{}'), marca, NOME[nome],
                      m['media_estrita_oito'], m['rival_decisiva_sem_alinhados'],
                      fora, m['rival_n_comparacoes']))

    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{The seventeen operations of the auxiliary comparison in '
        'Section~4.2 of the main text. \\textbf{\\emph{Accuracy} is the same quantity '
        'the source-level synthesis (Section~4.7) of the main text reports}: strict accuracy in per cent, ties counted as '
        'errors, '
        'averaged over all eight transformation types, on the 800 original--transformed '
        'comparisons. \\emph{Aligned-excluded} is a second aggregation of the same '
        'measurement, reported here because it appears elsewhere in this supplement: it '
        'drops ties from the denominator and averages only over the types not aligned by '
        'construction with the operation, which differ from row to row, so it rests on '
        'the smaller number of comparisons in the last column. \\emph{Excluded} names those '
        'types and \\emph{Pairs} counts the comparisons they leave, \\textbf{before ties '
        'are removed}, so the denominator that aggregation actually uses is smaller again '
        'wherever the operation ties. \\textbf{The two aggregations are not '
        'interchangeable}: relative to the canonical column the second is higher for some '
        'operations, lower for others and equal where neither ties nor alignment applies. '
        'Both columns are derived from the same pair-level measurements. A double dagger '
        'marks the %s '
        'sequence operations, which the isolated-frame inclusion rule excludes from the '
        'directional inventory and which enter only this auxiliary comparison. Under the '
        'canonical aggregation %d of the seventeen fall below SIFT+BoVW at %.1f\\%% and '
        'the median is %.1f\\%%; over the %d of the directional inventory alone the count '
        'is %d and the median %.1f\\%%. Identifiers in \\texttt{typewriter} are '
        'function names in the released package, kept verbatim so each row can be '
        'matched to the code that produced it.}\n'
        % (POREXT[len(extras)], dez['abaixo'], d['implantada_pct'], dez['mediana'],
           qui['n'], qui['abaixo'], qui['mediana']) +
        '\\label{tab:dezessete}\n\\footnotesize\n\\setlength{\\tabcolsep}{3.5pt}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{3.0cm}'
        '>{\\raggedright\\arraybackslash}p{2.5cm}rr'
        '>{\\raggedright\\arraybackslash}p{1.35cm}r@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Identifier} & \\hd{Operation} & \\hd{Acc.} & '
        '\\hd{Aligned-ex.} & \\hd{Excluded} & \\hd{Pairs} \\\\\n\\midrule\n'
        + '\n'.join(out) +
        '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  17 operacoes na regua canonica: %d abaixo de %.1f, mediana %.1f -> %s'
          % (dez['abaixo'], d['implantada_pct'], dez['mediana'], SAIDA.name))


if __name__ == '__main__':
    main()
