#!/usr/bin/env python3
"""A TABELA DO PROTOCOLO DE IDENTIFICACAO DAS OPERACOES (S31).

POR QUE EXISTE (12/09/2026). Um revisor observou que o artigo fala em «the literature» e
«the class» sem dizer como os trabalhos-fonte foram achados, e que sem isso nao ha como
saber o alcance das afirmacoes. ⭐ O levantamento EXISTIA em disco desde 05/09 e nunca
entrara no artigo: acervo, varredura por termo, validacao da propria varredura contra
leitura manual, criterio de triagem e auditoria de cobertura.

⭐ O que esta tabela tem e uma revisao de escopo comum nao tem: a ACURACIA DO PROPRIO
INSTRUMENTO DE BUSCA, medida contra um leitor, com a direcao do vies declarada.

Fonte: quatro JSON do benchmark. Nada e digitado.
"""
import os
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_protocolo.tex'
DATA = '5 September 2026'


def main():
    acv = json.loads((QB / 'o_que_os_173_usam_no_lugar.json').read_text(encoding='utf-8'))
    vrr = json.loads((QB / 'a_varredura_sem_a_bibliografia.json').read_text(encoding='utf-8'))
    cob = json.loads((QB / 'as_15_do_artigo_cobrem_o_que_o_campo_usa.json').read_text(encoding='utf-8'))
    acc = json.loads((QB / 'o_acervo_com_o_varredor_consertado.json').read_text(encoding='utf-8'))
    tri = cob['⭐_A_TRIAGEM_TEM_CRITERIO']
    c15 = cob['COBERTURA_DAS_15']

    # ⛔ zero esperado e bug ate prova em contrario: se qualquer perna vier vazia, a
    # tabela nao sai. Foi assim que um agregado vazio virou numero plausivel em 21/08.
    for nome, v in (('n_pdfs', acv['n_pdfs']), ('validados', vrr['n_artigos']),
                    ('triadas', tri['triadas']), ('mencoes', cob['mencoes_totais'])):
        assert v, '⛔ %s veio vazio: a tabela nao sai' % nome
    assert cob['mencoes_totais'] == c15['mencoes_cobertas'] + c15['mencoes_fora'], \
        '⛔ as mencoes nao fecham'
    assert (cob['fora_da_triagem']['por_direcao_nao_declarada']
            + cob['fora_da_triagem']['por_regra_de_combinacao_ausente']
            == c15['nao_triaveis_por_fonte_subespecificada']), '⛔ os nao triaveis nao fecham'

    termos = acc['ANTES']['por_termo']
    linhas = [
        ('Corpus', 'Curated full-text archive on video and multi-document summarization '
         'and on image-quality assessment, searched on %s. \\textbf{Not a database query, '
         'so the population of inference is this archive.}' % DATA,
         '%d PDFs' % acv['n_pdfs']),
        ('Patterns', 'One specific expression per operation family, never a bare word, so '
         'that \\emph{contrast} alone does not match. Reference lists are cut before '
         'matching; a cut leaving under 40\\,\\% of the PDF is refused and the work enters '
         'whole. Spatial information counts only when its context window carries ITU, the '
         'SI/TI pair, \\emph{index} or Sobel.',
         '%d patterns' % len(termos)),
        ('Instrument accuracy', 'Measured against a manual reading of the sources. '
         '\\textbf{The reading and the inventory were done by the same author}, so the '
         'estimates may be optimistic. \\textbf{The assessed articles are not a random '
         'sample of the archive}: they are the source works of the inventory together '
         'with articles selected because their combinations came closest to passing, and '
         'the second group inflates false positives by construction, so precision is not '
         'an unbiased estimate for the archive as a whole. Cutting reference '
         'lists raised precision from %s without moving recall.'
         % ('%.2f' % vrr['ANTES']['precisao']).lstrip('0'),
         'recall %s, precision %s, on %d articles'
         % (('%.2f' % vrr['DEPOIS']['cobertura']).lstrip('0'),
            ('%.2f' % vrr['DEPOIS']['precisao']).lstrip('0'), vrr['n_artigos'])),
        ('Inventory inclusion rule', 'An operation enters only if its source declares a '
         'direction for its own statistic and scores a single frame. \\textbf{No operation '
         'without a declared direction was screened in.} The %d that declare a direction '
         'and stay out are sequence-level: %s.'
         % (len(tri['com_direcao_mas_fora_da_triagem']),
            ', '.join('\\texttt{%s}' % x.replace('_', '\\_')
                      for x in tri['com_direcao_mas_fora_da_triagem'])),
         '%d of %d mapped operations' % (tri['triadas'], tri['no_mapa'])),
        ('Coverage achieved', 'Share of the operation mentions in the archive that the '
         'screened set covers. A mention is not an article: one PDF may name several.',
         '%d of %d mentions (%.1f\\,\\%%)'
         % (c15['mencoes_cobertas'], cob['mencoes_totais'], c15['porcentagem'])),
        ('What is left out, and why', '\\textbf{Of the %d mentions outside, %d were '
         'excluded under the inventory inclusion rule}, because the source specifies no '
         'direction (%d) or no combination rule (%d).'
         % (c15['mencoes_fora'], c15['nao_triaveis_por_fonte_subespecificada'],
            cob['fora_da_triagem']['por_direcao_nao_declarada'],
            cob['fora_da_triagem']['por_regra_de_combinacao_ausente']),
         '%d of %d excluded'
         % (c15['nao_triaveis_por_fonte_subespecificada'], c15['mencoes_fora'])),
        ('What the archive does instead', 'The term sweep is an automated retrieval '
         'check over an archive assembled during the thesis research; it is not a '
         'systematic mapping, and a match implies no reading of the matched work. '
         'Works citing no dedicated no-reference quality '
         'model, and how many of those match the patterns of one of the audited operations. '
         '\\textbf{These are term matches, not confirmed use}: they were not read '
         'individually, and the same search precision applies here.',
         '%d of %d cite none; %d of those matched an operation pattern'
         % (acv['n_sem_nriqa_dedicado'], acv['n_pdfs'],
            acv['dos_sem_dedicado_quantos_usam_operacao'])),
    ]

    corpo = '\n'.join(
        r'%s\textbf{%s} & %s & %s \\' % ('\\rowcolor{rowlight}' if i % 2 else '', a, b, c)
        for i, (a, b, c) in enumerate(linhas))

    SAIDA.write_text(
        '%%%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name +
        '\\begin{table}[!ht]\n\\centering\n'
        '\\caption{How the audited operations were identified, and what the protocol does '
        'and does not reach. The operations were not assembled from a database query, so '
        'the population of inference is the archive named in the first row and every count '
        'in this table is a count within it; no claim of exhaustive coverage is made. '
        '\\textbf{The search instrument is itself measured against a manual reading, with '
        'the direction of the residual bias stated}, because a search whose accuracy is '
        'unknown cannot bound what it missed.}\n'
        '\\label{tab:protocolo}\n\\footnotesize\n\\setlength{\\tabcolsep}{4pt}\n'
        '\\renewcommand{\\arraystretch}{1.15}\n'
        '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{2.2cm}'
        '>{\\raggedright\\arraybackslash}p{6.6cm}'
        '>{\\raggedright\\arraybackslash}p{2.9cm}@{}}\n'
        '\\toprule\n\\rowcolor{headerblue}\n'
        '\\hd{Step} & \\hd{What was done} & \\hd{What it yielded} \\\\\n\\midrule\n'
        + corpo + '\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    print('  %d passos -> %s' % (len(linhas), SAIDA.name))


if __name__ == '__main__':
    main()
