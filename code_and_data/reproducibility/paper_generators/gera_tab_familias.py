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
import os
import json
import re
from pathlib import Path


# ⛔ `` comia o zero INTERNO: 40.5 virava 4.5.
# Tira so o zero a esquerda do ponto que nao vem depois de digito.
def sem_zero(t):
    """Sem zero a esquerda, e com MENOS de verdade em vez de hifen.

    ⛔ 27/09 (parecer): a tabela imprimia «-.074» com hifen de hifenizacao,
    enquanto o resto do artigo escreve «$-$». Dois sinais para a mesma coisa
    na mesma pagina, e o hifen e visivelmente mais curto.
    """
    t = re.sub(r'(?<![0-9])0\.', '.', t)
    return re.sub(r'(?<![$\\w])-(?=[.0-9])', r'$-$', t)


import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
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

    COMP = json.loads((QB / 'as_combinacoes_COMO_A_LITERATURA_PUBLICA.json')
                      .read_text(encoding='utf-8'))['por_combinacao']
    _g = [(c['generalizacao_koniq']['rho_alinhado'], ' + '.join(c['campos'])) for c in COMP]
    GEN_COMP, GEN_QUEM = max(_g)
    _p = [(c['generalizacao_koniq']['rho_alinhado'], ' + '.join(c['campos']))
          for c in COMP if c['media_z']['passa']]
    assert len(_p) == 1, '⛔ esperava exatamente um composto passando a sensibilidade'
    GEN_PASSA, GEN_PASSA_QUEM = _p[0]
    assert GEN_COMP > GEN_PASSA, ('⛔ o maximo deixou de ser maior que o do que passa: '
                                  'a nota da legenda precisa ser reescrita')

    # familia, n, melhor sensibilidade, melhor generalizacao, elegiveis, cor
    F = [(r'Low-level pixel heuristics', len(ops), h_sens, h_gen,
          f'{h_eleg} of {len(com)} evaluated',
          'focoauditado!12'),
         (r'Visual-word counting: SIFT+BoVW '
          r'\citep{barbieri2021tese}', 3, -0.077, -0.445, '0 of 1 evaluated',
          'focoauditado!12'),
         (r'Dedicated NR-IQA models', 10, 0.849, 0.723,
          r'\textbf{3 of 10}', 'accentgreen!14'),
         (r'Deep representativeness proxies', 3, None, None,
          r'\textcolor{black!45}{not screened} (Section~\ref{sec:taxonomy_results})', 'focoauditado!7'),
         (r'REGUA', None, None, None, None, None),
         (r'\emph{Attribute configurations (diagnostic)}$^{\star}$', len(COMP),
          SENS_COMP, GEN_COMP,
          r'0 of %d \ \tiny(1 clears sens.)' % len(COMP), 'rowlight')]

    GEN_PASSA_TXT = ('%.3f' % GEN_PASSA).lstrip('0')

    L = [r'\begin{table}[!ht]', r'\centering',
         # ⛔ `\ref` NAO atravessa documentos: esta tabela vive no suplementar e o rotulo
         # ⭐ 21/09: a tabela subiu para o CORPO, entao o ponteiro volta a ser `\ref`
         # e o numero da secao deixa de ser digitado. Enquanto ela vivia no
         # suplementar, `\ref` nao alcancava e o numero ia como texto.
         # ⛔ 21/09: a tabela subiu para o CORPO, e `\ref` NAO atravessa documento: os
         # tres rotulos do suplementar que a legenda citava davam «Reference undefined»
         # e numero vazio no PDF. Viram numero digitado, que e a convencao do corpo, e
         # o `sincroniza_ponteiros` os mantem em dia por ancora declarada.
         # ⛔ 21/09 (parecer, TB05, criterios 14, 15, 27, 29, 30, 42): o titulo dizia «the
         # three families» e a tabela tem CINCO linhas de agrupamento; «whose three
         # conditions» somava a confusao, porque a coluna resume DUAS; e havia um «two»
         # solto, resto de edicao, em «allowed for those configurations two».
         r'\caption{\textbf{External screening by method class} '
         r'(Table~\ref{tab:taxonomy}). Each cell is the maximum over its class on that '
         r'axis alone, so \textbf{the two maxima need not belong to the same member}. '
         r'\emph{Clears both external} counts the members passing sensitivity and '
         r'generalization together; \textbf{the in-domain floor is a third condition, '
         r'reported separately}. Spatial information declares no direction and carries no '
         f'verdict; the heuristics row counts {len(ops)} computed and {len(com)} '
         r'evaluated, and the bag-of-visual-words row 3 computed and 1 evaluated: '
         r'the other two, keypoint density and the 19-extractor ablation, are '
         r'diagnostics rather than published scores. '
         r'Deep proxies read context and fall outside the isolated-image '
         r'protocol (Section~\ref{sec:taxonomy_results}). The two source-specified rules are not '
         r'screened (Section~\ref{sec:combinations}). $^{\star}$Diagnostic, not a '
         r'published class: generalization is the KonIQ-10k association under a '
         r'data-derived orientation with normalization re-estimated per database, which '
         r'makes its zero conservative. Per-operation values are in the supplement.' + '}',
         r'\label{tab:families}', r'\small', r'\setlength{\tabcolsep}{7pt}',
         r'\renewcommand{\arraystretch}{1.0}',
         r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.5cm} c r r c@{}}', r'\toprule', r'\rowcolor{headerblue}',
         # ⭐ 22/09 (parecer v2, V2-063): «Family» repetia a palavra que a 2.2 usa para as
         # familias de MODELO, e a coluna agrupa por grupo avaliado; e «Clears both» tinha
         # de dizer QUAIS dois, para nao ser lido como elegibilidade das tres condicoes.
         r'\hd{Evaluated group} & \hd{$n$} & \hd{Best sens.} & \hd{Best gen.} & '
         r'\hd{Clears both external} \\',
         r'\midrule']
    for nome, k, s_, g_, e, cor in F:
        # ⭐ o fio separa as configuracoes: elas nao sao uma classe da literatura
        if nome == 'REGUA':
            L.append(r'\midrule')
            continue
        L.append(f'\\rowcolor{{{cor}}}{nome} & {k} & {n(s_)} & {n(g_)} & {e} \\\\')
    L += [r'\midrule',
          r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(F)} familias -> {SAIDA.name}')


if __name__ == '__main__':
    main()
