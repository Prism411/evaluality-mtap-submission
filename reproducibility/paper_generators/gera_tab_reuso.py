#!/usr/bin/env python3
"""A TABELA DE ORIGEM, USO E OBJETO AVALIADO.

POR QUE EXISTE (08/09/2026). Uma citacao a fonte NAO responde tres perguntas que o artigo
precisa separar, e que estavam coladas no texto:
  1. ORIGEM: que trabalho define a expressao;
  2. USO NA SELECAO: que trabalho a usa num componente de selecao, e em qual componente;
  3. OBJETO AVALIADO: o que a nossa bancada de fato mede — o modulo, o termo isolado, ou
     uma adaptacao nossa.

⛔ O criterio de fechamento: toda afirmacao de «a literatura usa» aponta um consumidor
IDENTIFICAVEL, e toda adaptacao nossa esta rotulada como adaptacao. As linhas abaixo so
entram com trecho conferido no PDF da fonte; o que nao foi conferido nao vira linha.
"""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_reuso.tex'

# (rotulo, origem+papel, uso documentado em selecao, objeto avaliado, verificado em)
LINHAS = [
    (r'Edge distribution, hue count, contrast',
     r'\citet{ke2006highlevel}: features of a naive Bayes classifier for photo quality',
     r'\citet{srinivas2016rank} cites Ke for all three (\S3.1.3--3.1.5) and averages them '
     r'into a per-frame quality score',
     r'each term alone, plus the mean and an adapted classifier'),
    (r'Colourfulness in that same score',
     r'Swain and Ballard, by histogram intersection, as \citet{srinivas2016rank} states',
     r'\citet{srinivas2016rank}, \S3.1.1',
     r'the Hasler expression instead, a declared substitution'),
    (r'Sharpness and brightness',
     r'\citet{korolkov2025keyframe}: two terms of a keyframe score',
     r'the same work, $0.7\,z(\mathrm{sharp})+0.3\,z(\mathrm{bright})$',
     r'the published rule, with our normalization population stated'),
    (r'Contrast variance',
     r'\citet{jeong2016static}: a badness term inside a cost multiplicative in cluster '
     r'distance',
     r'the same work, within that objective',
     r'the isolated statistic, read in the increasing direction'),
    (r'Gradient magnitude, saliency, entropy, gradient orientation',
     r'\citet{qaroush2025diversity}: terms of four numbered objectives',
     r'the same work; two of the four objectives are not about visual quality',
     r'each term alone, and the visual-attention module of Eq.~20'),
]


def main():
    au = json.load(open(QB / 'quantas_sao_indice_autonomo_na_fonte.json'))
    L = [r'\begin{table}[!ht]', r'\centering',
         r'\caption{Origin, documented use and evaluated object for the cases that carry the '
         r'claims here. \textbf{A citation does not say which work '
         r'used the operation in selection, nor what this bench measured}, so the three are '
         r'separated; where origin and use fall in the same work the middle column says so, '
         r'and the last column marks our own adaptations as such. The full inventory, with '
         r'formulas and results files, is in Tables~S17 and~S23.}',
         r'\label{tab:reuse}', r'\footnotesize', r'\setlength{\tabcolsep}{4pt}',
         r'\renewcommand{\arraystretch}{1.12}',
         r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.5cm}'
         r'>{\raggedright\arraybackslash}p{3.5cm}'
         r'>{\raggedright\arraybackslash}p{3.4cm}'
         r'>{\raggedright\arraybackslash}p{3.3cm}@{}}', r'\toprule',
         r'\rowcolor{headerblue}',
         r'\hd{Operation} & \hd{Origin and role there} & \hd{Documented use in selection} & '
         r'\hd{Evaluated here} \\', r'\midrule']
    for i, (op, orig, uso, aval) in enumerate(LINHAS):
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        L.append(f'{cor}{op} & {orig} & {uso} & {aval} \\\\')
    L += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(LINHAS)} cadeias -> {SAIDA.name}')


if __name__ == '__main__':
    main()
