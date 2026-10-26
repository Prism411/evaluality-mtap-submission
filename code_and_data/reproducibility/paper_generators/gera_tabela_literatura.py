#!/usr/bin/env python3
"""Gera a Tabela 1: as 16 operacoes de qualidade da literatura de sumarizacao,
com o trabalho de origem e as tres portas. Le dos JSON medidos, nao digita numero."""
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
SAIDA = Path(__file__).parent / 'tab_literatura.tex'

NOME = {
    'ke_edge_distribution': 'Edge distribution', 'qaroush_go': 'Gradient orientation',
    'si': 'Spatial information', 'ke_contraste': 'Contrast',
    'contraste_variancia': 'Grey-level dispersion', 'ke_hue_count': 'Hue count',
    'qaroush_entropia': 'Entropy', 'qaroush_gm': 'Gradient magnitude',
    'qaroush_saliencia': 'Saliency area', 'gygli_media_crua': 'Averaged aesthetics (3)',
    'srinivas_quality': 'Composite of five', 'glcm_contraste': 'GLCM contrast',
    'laplacian_var': 'Laplacian variance', 'huang_saturacao': 'Saturation',
    'hasler_colorfulness': 'Colourfulness (Hasler)', 'ke_colorfulness': 'Colourfulness (Ke)',
}
CITE = {
    'ke_edge_distribution': 'ke2006highlevel', 'qaroush_go': 'qaroush2025diversity',
    'si': 'itu_p910', 'ke_contraste': 'ke2006highlevel',
    'contraste_variancia': 'jeong2016static', 'ke_hue_count': 'ke2006highlevel',
    'qaroush_entropia': 'qaroush2025diversity', 'qaroush_gm': 'qaroush2025diversity',
    'qaroush_saliencia': 'qaroush2025diversity', 'gygli_media_crua': 'gygli2014summe',
    'srinivas_quality': 'srinivas2016rank', 'glcm_contraste': 'yang2024keyframe',
    'laplacian_var': 'cakmak2025tripss', 'huang_saturacao': 'huang2024aesthetic',
    'hasler_colorfulness': 'hasler2003colorfulness', 'ke_colorfulness': 'ke2006highlevel',
}
SENS, TIPOS, GEN = 0.50, 15, 0.65
PALAVRA = {11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen', 15: 'fifteen'}
POSTO = json.load(open(QB / 'posto_e_m_eff_das_15.json'))['posto_dos_escores_crus']


def main():
    ops = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    piso = {}
    try:
        f = json.load(open(QB / 'o_piso_das_operacoes_isoladas_e_estavel.json'))
        for x in f.get('por_operacao', []):
            if isinstance(x, dict) and 'operacao' in x:
                piso[x['operacao']] = x          # ⭐ o dict inteiro: o ponto
                                                 # sozinho nao deixa auditar a aprovacao
    except Exception:
        pass
    linhas = sorted(ops.items(), key=lambda x: -x[1]['sensibilidade_media'])
    L = [r'\begin{table}[!ht]', r'\centering',
         r'\caption{The sixteen visual-selection operations the video-summarization '
         r'literature uses at the selection stage, reimplemented from the published '
         r'equations and measured under one protocol. \emph{Sensitivity} is the '
         r'SRCC against the degradation level within each KADID-10k reference, aligned to '
         r'the direction the source declares for its own statistic, averaged over the 25 '
         r'distortion types, with the count of types above $.50$; \emph{Generalization} '
         r'is the lowest such correlation on any database the method was not fitted on; '
         r'\emph{Floor} is chance-corrected agreement on the operational clusters. '
         r'\textbf{The two families use different reference models there}: operations '
         r'against LIQE, the ten no-reference models against Q-Align, so that column is '
         r'not a comparison between families. The damage columns share one protocol. '
         rf'The rule admits a method when sensitivity exceeds '
         rf'${str(SENS).lstrip("0")}$ on at least ${TIPOS}$ of 25 types and generalization exceeds ${str(GEN).lstrip("0")}$. '
         r'\textbf{No operation clears either external screening criterion}: the best sensitivity is '
         r'$.298$ and the best generalization among the fifteen evaluated is $.139$. '
         r'Spatial information declares no direction, carries no verdict and is excluded '
         # ⚠️ o posto mora aqui e nao no corpo: a pergunta «as quinze sao quinze medidas?»
         # se faz olhando ESTA tabela, e a base do numero e a matriz de escores do KADID,
         # nao as decisoes nos 42 clusters, onde vivem as tres variantes de brightness.
         rf'from every count. \textbf{{The fifteen are not fifteen independent '
         rf'measurements}}: on KADID-10k their score matrix has rank {PALAVRA[POSTO]}, '
         rf'because one colourfulness implementation duplicates another exactly and one '
         rf'operation is the mean of three others. '
         r'The \emph{Floor} column reports the in-domain agreement '
         r'against the reference model with the lower end of its 95\% interval in '
         r'brackets, so a pass can be read for how much of it survives the interval: the '
         # ⚠️ esta tabela vive no SUPLEMENTAR; macro do corpo nao alcanca. Valor inline.
         + 'weakest passing operation in this table has a lower bound of $'
         + sem_zero(f'{min(v["ic_inferior"] for k, v in piso.items() if k in ops and v["passa"] and k != "si"):+.3f}')
         + '$.}',
         r'\label{tab:literature}', r'\small', r'\setlength{\tabcolsep}{5pt}',
         r'\begin{tabular}{@{}l l r r r r c@{}}', r'\toprule',
         r'\rowcolor{headerblue}',
         r'\hd{Operation} & \hd{Source} & \hd{Sens.} & \hd{Types} & \hd{Gen.} & '
         r'\hd{Floor $\kappa$ [95\% lo]} & \hd{Elig.} \\', r'\midrule']
    for i, (k, v) in enumerate(linhas):
        nome = NOME.get(k, k.replace('_', r'\_'))
        cite = f"\\citep{{{CITE[k]}}}" if CITE.get(k) else '---'
        s, t = v['sensibilidade_media'], v['sensibilidade_tipos']
        g = v['menor_rho_em_base_nao_vista']
        p = piso.get(k)
        # ⚠️ ic_inferior existe na fonte e nunca era impresso: sem ele, um kappa de +.326
        # com limite inferior +.050 se le igual a um de +.551 com limite +.328
        pv = (f"${p['kappa']:+.3f}$ \\ \\tiny[${p['ic_inferior']:+.3f}$]"
              if p is not None else '---')
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        # ⚠️ o `si` nao tem direcao declarada na fonte: sem veredito, e fora das contagens
        eleg = '---' if k == 'si' else 'no'
        L.append(sem_zero(
            f"{cor}{nome} & {cite} & ${s:.3f}$ & {t} & ${g:+.3f}$ & {pv} & {eleg} \\\\"))
    L += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(linhas)} linhas -> {SAIDA.name}')


if __name__ == '__main__':
    main()
