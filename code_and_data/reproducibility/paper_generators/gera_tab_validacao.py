#!/usr/bin/env python3
"""A TABELA DOCUMENTAL: o que cada trabalho-fonte apresenta como evidencia, com o trecho.

POR QUE EXISTE (08/09/2026). A Tabela 3 do corpo diz, numa clausula por banda, o que a fonte
testa. Essa afirmacao e sobre o artigo de outra pessoa, entao ela precisa ser AUDITAVEL: aqui
fica o trecho literal do PDF que a sustenta, fonte por fonte.

⛔ A regra que governa esta tabela: «nao consta no acervo» NAO e «nao validou». As duas fontes
sem PDF entram numa linha propria, sem veredito.
"""
import os
import json
import re
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_validacao.tex'

CITE = {
    'ke2006highlevel': 'ke2006highlevel', 'hasler2003colorfulness': 'hasler2003colorfulness',
    'srinivas2016rank': 'srinivas2016rank', 'qaroush2025diversity': 'qaroush2025diversity',
    'korolkov2025keyframe': 'korolkov2025keyframe', 'cakmak2025tripss': 'cakmak2025tripss',
    'yang2024keyframe': 'yang2024keyframe', 'huang2024aesthetic': 'huang2024aesthetic',
    'jeong2016static': 'jeong2016static', 'gygli2014summe': 'gygli2014summe',
    'xu2024property': 'xu2024property',
}

ROTULO = {
    'julgamento humano da propriedade': (r'\textbf{human judgement of the property}', 'perf5!35'),
    'so o resumo': ('the summary only', 'perf2!45'),
    'so o resumo, com ablacao de modulo': ('the summary, with an ablation', 'perf3!55'),
    # ⭐ 25/09 (parecer v11, §4): o rotulo curto do Jeong dizia so «the summary only»
    #    enquanto a descricao ja reconhecia a variante sem otimizacao.
    'so o resumo, com ablacao de etapa': ('the summary, with an optimisation ablation',
                                          'perf3!55'),
    'nem a regra nem os pesos': (r'\textbf{neither the rule nor its weights}', 'perf1!45'),
}

# a leitura em portugues do arquivo de apuracao, dita em ingles para o artigo
RESUMO = {
    'ke2006highlevel':
        'community ratings on 60{,}000 photos as ground truth; per-feature '
        'precision--recall and a combined classifier at 27.8 per cent equal error, '
        'on the extremes only',
    'hasler2003colorfulness':
        'a psychophysical scaling experiment, seven categories, the expression fitted '
        'to the ratings at 94.0 per cent; the property is colourfulness',
    'srinivas2016rank':
        'precision, recall and F of the selected keyframes against the ground-truth '
        'keyframes of seven open-video.org videos',
    'qaroush2025diversity':
        'precision, recall and F1 of the extracted segments against reference summaries',
    'korolkov2025keyframe':
        'weights set, not fitted; ablations vary segmentation parameters, and keyframes '
        'are judged by coverage and a qualitative review',
    'cakmak2025tripss':
        'TVSum20 and SumMe against human importance scores, with an ablation removing '
        'each modality',
    'yang2024keyframe':
        'structural and feature ablations scored by F on SumMe over 15 annotations',
    'xu2024property':
        'F against summaries from five users on OVP, with an ablation of the frame-block '
        'length; no isolated test of the entities or of their weights',
    'huang2024aesthetic':
        'Spearman and Kendall rank correlation against human annotations on four datasets, '
        'in canonical, augmentation and transfer setups',
    'jeong2016static':
        'summary-level human evaluation and precision/recall against labelled events, with '
        'a comparison against an optimisation-removed variant; the component-level claim '
        'here concerns the isolated grey-level statistic, which is not tested alone',
    'gygli2014summe':
        'f-measure against multiple human-created summaries per video, collected in a study '
        'with perception psychologists, plus an ablation measuring the gain of adding each '
        'feature to the set',
}


def escapa(s):
    return s.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')


def main():
    d = json.load(open(QB / 'o_que_cada_fonte_valida.json'))
    L = [r'%% GERADO por gera_tab_validacao.py. Nao editar a mao.',
         r'\begin{table}[p]', r'\centering',
         r'\caption{\textbf{What each source work reports as evidence for its own visual '
         r'criterion.} Read from the full text of each paper; the excerpt is verbatim. '
         r'\emph{Tests} names what the source puts to a test, which is not always the '
         r'operation the later literature borrows. One of the eleven source works is not in '
         r'our archive and carries no verdict here: \textbf{absence of a reading is not '
         r'absence of validation}. It documents the clause carried on each band of the audit table '
         r'in the main text.}',
         r'\label{tab:validation}', r'\scriptsize',
         r'\setlength{\tabcolsep}{2.6pt}', r'\renewcommand{\arraystretch}{0.96}',
         r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.1cm}'
         r'>{\raggedright\arraybackslash}p{2.4cm}'
         r'>{\raggedright\arraybackslash}p{3.5cm}'
         r'>{\raggedright\arraybackslash}p{3.6cm}@{}}',
         r'\toprule', r'\rowcolor{headerblue}',
         r'\hd{Source} & \hd{Tests} & \hd{What it reports} & \hd{Verbatim excerpt} \\',
         r'\midrule']

    n = 0
    for k, v in d['por_fonte'].items():
        rot, cor = ROTULO[v['tipo']]
        # ⛔ em aspas SIMPLES o `\'\'` fecharia a string e o resto deixaria de ser raw:
        # foi assim que o `\\\\` do fim da linha virou uma barra so e a tabela quebrou.
        onde = v.get('onde')
        loc = (r' \textnormal{(%s)}' % escapa(onde)) if onde else ''
        L.append(r"\rowcolor{%s}\citet{%s} & %s & %s & \emph{``%s''}%s \\"
                 % (cor, CITE[k], rot, escapa(RESUMO[k]),
                    escapa(v['verbatim'].replace('...', r'\,\ldots\,')), loc))
        n += 1

    L.append(r'\midrule')
    for k in d['sem_pdf_no_acervo']:
        L.append(r'\rowcolor{black!5}\citet{%s} & \textcolor{black!55}{not read} & '
                 r'\multicolumn{2}{@{}l}{\textcolor{black!55}{no PDF in our archive, so no '
                 r'verdict is recorded}} \\' % CITE[k])
        n += 1

    L += [r'\bottomrule', r'\end{tabular}', r'\end{table}']

    # ⭐ corta em duas: acha o cabecalho e repete-o na segunda parte
    i_mid = L.index(r'\midrule')
    corpo = [x for x in L[i_mid + 1:] if x.startswith(r'\rowcolor') or x == r'\midrule']
    metade = len(corpo) // 2
    cabeca = L[:i_mid + 1]
    rabo = [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    parte1 = cabeca + corpo[:metade] + rabo
    # a segunda parte repete o cabecalho com legenda curta e sem repetir a nota longa
    cab2 = []
    for x in cabeca:
        if x.startswith(r"\caption{"):
            cab2.append(r'\caption{\textbf{Evidence reported by each source work, continued.} '
                        r'Columns as in the preceding table.}')
        elif x.startswith(r'\label{'):
            cab2.append(r'\label{tab:validation_b}')
        else:
            cab2.append(x)
    parte2 = cab2 + corpo[metade:] + rabo
    SAIDA.write_text('\n'.join(parte1) + '\n\n' + '\n'.join(parte2) + '\n', encoding='utf-8')
    print('  escrito %s  (%d fontes: %d lidas, %d sem PDF)'
          % (SAIDA.name, n, d['n_com_pdf'], d['n_sem_pdf']))


if __name__ == '__main__':
    main()
