#!/usr/bin/env python3
"""A TABELA DOCUMENTAL: o que cada trabalho-fonte apresenta como evidencia, com o trecho.

POR QUE EXISTE (08/09/2026). A Tabela 3 do corpo diz, numa clausula por banda, o que a fonte
testa. Essa afirmacao e sobre o artigo de outra pessoa, entao ela precisa ser AUDITAVEL: aqui
fica o trecho literal do PDF que a sustenta, fonte por fonte.

⛔ A regra que governa esta tabela: «nao consta no acervo» NAO e «nao validou». As duas fontes
sem PDF entram numa linha propria, sem veredito.
"""
import json
import re
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_validacao.tex'

CITE = {
    'ke2006highlevel': 'ke2006highlevel', 'hasler2003colorfulness': 'hasler2003colorfulness',
    'srinivas2016rank': 'srinivas2016rank', 'qaroush2025diversity': 'qaroush2025diversity',
    'korolkov2025keyframe': 'korolkov2025keyframe', 'cakmak2025tripss': 'cakmak2025tripss',
    'yang2024keyframe': 'yang2024keyframe', 'huang2024aesthetic': 'huang2024aesthetic',
    'jeong2016static': 'jeong2016static', 'gygli2014summe': 'gygli2014summe',
}

ROTULO = {
    'julgamento humano da propriedade': (r'\textbf{human judgment of the property}', 'perf5!35'),
    'so o resumo': ('the summary only', 'perf2!45'),
    'so o resumo, com ablacao de modulo': ('the summary, with an ablation', 'perf3!55'),
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
    'huang2024aesthetic':
        'Spearman and Kendall rank correlation against human annotations on TVSum and SumMe',
    'jeong2016static':
        'mean opinion scores from human subjects and precision/recall against labeled '
        'events; no ablation or isolated test of the contrast term',
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
         r'\begin{table}[!ht]', r'\centering',
         r'\caption{\textbf{What each source work reports as evidence for its own visual '
         r'criterion.} Read from the full text of each paper; the excerpt is verbatim. '
         r'\emph{Tests} names what the source puts to a test, which is not always the '
         r'operation the later literature borrows. Two sources are not in our archive and '
         r'therefore carry no verdict: \textbf{absence of a reading is not absence of '
         r'validation}. It documents the clause carried on each band of the audit table '
         r'in the main text.}',
         r'\label{tab:validation}', r'\scriptsize',
         r'\setlength{\tabcolsep}{3pt}', r'\renewcommand{\arraystretch}{1.02}',
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
        L.append(r"\rowcolor{%s}\citet{%s} & %s & %s & \emph{``%s''} \\"
                 % (cor, CITE[k], rot, escapa(RESUMO[k]),
                    escapa(v['verbatim'].replace('...', r'\,\ldots\,'))))
        n += 1

    L.append(r'\midrule')
    for k in d['sem_pdf_no_acervo']:
        L.append(r'\rowcolor{black!5}\citet{%s} & \textcolor{black!55}{not read} & '
                 r'\multicolumn{2}{@{}l}{\textcolor{black!55}{no PDF in our archive, so no '
                 r'verdict is recorded}} \\' % CITE[k])
        n += 1

    L += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('  escrito %s  (%d fontes: %d lidas, %d sem PDF)'
          % (SAIDA.name, n, d['n_com_pdf'], d['n_sem_pdf']))


if __name__ == '__main__':
    main()
