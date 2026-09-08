#!/usr/bin/env python3
"""A TABELA DE FAMILIAS: o resultado principal das tres familias, numa olhada.

POR QUE EXISTE (07/09/2026). A triagem por operacao ficava na Tabela 3 e a dos modelos
NR-IQA no suplementar, entao o leitor nao conseguia ver o resultado das familias sem
procurar em dois documentos. Esta tabela poe as tres lado a lado sob a MESMA regra, e o
detalhe por operacao e por modelo continua no suplementar.

⚠️ O que ela NAO faz: nao mistura eixos. Os modulos reproduzidos (Qaroush, Korolkov) foram
medidos na bancada pareada e nao nas duas portas de dano, entao entram com a coluna que
possuem e um travessao nas que nao possuem. Inventar um valor para preencher a linha seria
o defeito que este artigo audita.
"""
import json
import re
from pathlib import Path


# ⛔ `` comia o zero INTERNO: 40.5 virava 4.5.
# Tira so o zero a esquerda do ponto que nao vem depois de digito.
def sem_zero(t):
    return re.sub(r'(?<![0-9])0\.', '.', t)


QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_familias.tex'
SENS, TIPOS, GEN = 0.50, 15, 0.65
SENS_COMP = 0.524   # o composto que passa a porta de sensibilidade


def num_do_suplementar(rotulo, alternativa='S?'):
    """⭐ O S-numero que o suplementar de fato produziu. Digitar aqui envelhece: a
    numeracao mudou cinco vezes numa noite conforme tabelas entravam e saiam."""
    aux = Path(__file__).parent / 'supplementary.aux'
    if not aux.exists():
        return alternativa
    m = re.search(r'\\newlabel\{' + re.escape(rotulo) + r'\}\{\{(S\d+)\}', aux.read_text())
    return m.group(1) if m else alternativa


def n(x, casas=3):
    return sem_zero(f'${x:+.{casas}f}$') if x is not None else '---'


def main():
    ops = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    va = json.load(open(QB / 'o_vascore_do_qaroush_como_a_Eq20_manda.json'))
    ko = json.load(open(QB / 'o_modulo_do_korolkov_nos_11_segmentos.json'))
    com = [k for k in ops if k != 'si']
    h_sens = max(ops[k]['sensibilidade_media'] for k in com)
    h_gen = max(ops[k]['menor_rho_em_base_nao_vista'] for k in com
                if ops[k].get('menor_rho_em_base_nao_vista') is not None)
    h_eleg = sum(1 for k in ops if ops[k].get('elegivel'))

    # familia, n, melhor sensibilidade, melhor generalizacao, elegiveis, cor
    F = [(r'Summarization heuristics', len(ops), h_sens, h_gen,
          f'{h_eleg} of {len(com)} evaluated',
          'catbovw!12'),
         (r'Published composites', 19, SENS_COMP, 0.067,
          r'0 of 19 \ \tiny(1 clears sens.)', 'catbovw!7'),
         (r'Reproduced modules', 2, None, None, r'\textcolor{black!45}{not screened}',
          'catbovw!7'),
         (r'No-reference models', 10, 0.849, 0.723, r'\textbf{3 of 10}', 'accentgreen!14'),
         (r'Deployed SIFT+BoVW', 1, -0.077, -0.445, '0 of 1', 'rowlight')]

    L = [r'\begin{table}[!ht]', r'\centering',
         # ⛔ `\ref` NAO atravessa documentos: esta tabela vive no suplementar e o rotulo
         # `sec:screen` e do corpo. O numero entra como texto.
         r'\caption{The three families under the screening rule of Section~3.5 of the main '
         r'text, whose three conditions are stated there. '
         r'\textbf{Each cell is the maximum over its family on that axis alone}, and the '
         r'two maxima need not belong to the same member: among the no-reference models '
         r'the best sensitivity is QualiCLIP and the best generalization LIQE. Spatial '
         r'information declares no direction and the reproduced modules were measured on '
         r'the constructed pairs rather than on these axes, so neither carries a verdict '
         r'here; the heuristics row counts 16 computed and 15 evaluated. Per-operation '
         r'values are in Table~S18 and per-model values in Table~S21.}',
         r'\label{tab:families}', r'\small', r'\setlength{\tabcolsep}{7pt}',
         r'\renewcommand{\arraystretch}{1.0}',
         r'\begin{tabular}{@{}l c r r c@{}}', r'\toprule', r'\rowcolor{headerblue}',
         r'\hd{Family} & \hd{$n$} & \hd{Best sens.} & \hd{Best gen.} & \hd{Clears both} \\',
         r'\midrule']
    for nome, k, s_, g_, e, cor in F:
        L.append(f'\\rowcolor{{{cor}}}{nome} & {k} & {n(s_)} & {n(g_)} & {e} \\\\')
    L += [r'\midrule',
          r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(F)} familias -> {SAIDA.name}')


if __name__ == '__main__':
    main()
