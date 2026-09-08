#!/usr/bin/env python3
"""A SINTESE DA AUDITORIA, ORGANIZADA POR TRABALHO-FONTE (nao por operacao).

POR QUE EXISTE (08/09/2026). O artigo respondia bem «esta operacao inverte sob ruido?»
e mal «o que ESTE TRABALHO faz, e o que a nossa auditoria encontrou nele?». Para
descobrir o segundo o leitor tinha de ler o texto inteiro e remontar o mapa de cabeca.

Esta peca inverte a organizacao: a linha e o TRABALHO e o componente, as oito colunas
sao as degradacoes, e a cor entrega o padrao antes da leitura.

⛔ TRES REGRAS, e elas mudam o que a tabela pode dizer:
  1. o papel na fonte vem de trecho conferido no PDF; o que nao foi conferido nao vira linha;
  2. quando dois trabalhos usam A MESMA computacao (laplacian_var em Korolkov e em Cakmak),
     o numero aparece nos dois, marcado, e NAO conta como evidencia independente;
  3. «reprova como escore de qualidade» nunca vira «o trabalho errou»: o veredito e sempre
     do objeto que a bancada mediu, com o papel original ao lado.

Nenhum numero e digitado: todos saem do JSON medido.
"""
import json, re, sys
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_sintese.tex'

TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']
CABECA = ['Dk', 'Mo', 'Bl', 'H2', 'Rs', 'St', 'Ns', 'Jp']


def sem_zero(t):
    # ⛔ `.replace('0.', '.')` comia o zero INTERNO: 40.5 virava 4.5.
    return re.sub(r'(?<![0-9])0\.', '.', t)


def cor(a):
    """A paleta perf1..perf5 que o artigo ja usa, do vermelho ao verde."""
    if a is None:
        return 'black!6'
    if a < 20:  return 'perf1!70'
    if a < 40:  return 'perf2!70'
    if a < 60:  return 'perf3!80'
    if a < 80:  return 'perf4!70'
    return 'perf5!45'


def celula(a, alinhado):
    if a is None:
        return r'\cellcolor{black!6}{\tiny --}'
    txt = '%d' % round(a)
    if alinhado:
        # ⚠️ a degradacao age DIRETAMENTE na grandeza que a operacao mede. A celula fica
        # marcada porque o leitor precisa saber disso, e NAO porque o acerto valha menos:
        # uma medida de nitidez responder ao desfoque pode ser justamente a propriedade
        # que se quer verificar. A marca informa; ela nao desconta.
        return (r'\cellcolor{%s}\textcolor{black!75}{\itshape %s}\rlap{\tiny$^{*}$}'
                % (cor(a), txt))
    return r'\cellcolor{%s}%s' % (cor(a), txt)


# ---------------------------------------------------------------------------
# O papel na fonte. Cada string abaixo resume um trecho JA conferido no PDF da
# fonte (mesmo criterio de fechamento de `gera_tab_reuso.py`).
# ---------------------------------------------------------------------------
TRABALHOS = [
    dict(chave='ke2006highlevel',
         titulo=r'\citet{ke2006highlevel}',
         papel=r'four features of a naive Bayes photo-quality classifier',
         ops=[('ke_edge_distribution', 'Edge distribution'),
              ('ke_hue_count',         'Hue count'),
              ('ke_contraste',         'Contrast'),
              ('ke_colorfulness',      r'Colourfulness$^{\ddagger}$')],
         objeto=r'each feature alone, as a score'),

    dict(chave='srinivas2016rank',
         titulo=r'\citet{srinivas2016rank}',
         papel=r'averages five attributes into a per-frame quality score',
         ops=[('srinivas_quality', r'The mean rule, our vector')],
         objeto=r'its mean rule, on our attribute vector'),

    dict(chave='qaroush2025diversity',
         titulo=r'\citet{qaroush2025diversity}',
         papel=r'four terms across three objectives',
         ops=[('__VASCORE__',       'Visual-attention module'),
              ('qaroush_gm',        r'\quad Gradient magnitude'),
              ('qaroush_saliencia', r'\quad Saliency'),
              ('qaroush_ct',        r'\quad Contrast term'),
              ('qaroush_entropia',  'Entropy'),
              ('qaroush_go',        'Gradient orientation')],
         objeto=r'the module as published, then each term'),

    dict(chave='korolkov2025keyframe',
         titulo=r'\citet{korolkov2025keyframe}',
         papel=r'$0.7\,z(\mathrm{sharp})+0.3\,z(\mathrm{bright})$ as a keyframe score, \textbf{on 11 of the 20 segments}',
         ops=[('__KOROLKOV__',       'The published rule'),
              ('__KOROLKOV_SHARP__', r'\quad Sharpness alone, same 11$^{\dagger}$')],
         objeto=r'the rule, our normalization population'),

    dict(chave='cakmak2025tripss',
         titulo=r'\citet{cakmak2025tripss}',
         papel=r'a threshold discarding blurred frames, not a score',
         ops=[('laplacian_var', r'Laplacian variance$^{\dagger}$')],
         objeto=r'the statistic as a scorer, not the filter'),

    dict(chave='jeong2016static',
         titulo=r'\citet{jeong2016static}',
         papel=r'a badness term in a cost multiplicative in cluster distance',
         ops=[('contraste_variancia', 'Contrast variance')],
         objeto=r'the term, read increasing'),

    dict(chave='yang2024keyframe',
         titulo=r'\citet{yang2024keyframe}',
         papel=r'one texture term of several',
         ops=[('glcm_contraste', 'GLCM contrast')],
         objeto=r'the term alone'),

    dict(chave='huang2024aesthetic',
         titulo=r'\citet{huang2024aesthetic}',
         papel=r'one aesthetic attribute of several',
         ops=[('huang_saturacao', 'Saturation')],
         objeto=r'the attribute alone'),

    dict(chave='gygli2014summe',
         titulo=r'\citet{gygli2014summe}',
         papel=r'three aesthetic attributes averaged',
         ops=[('gygli_media_crua', 'Averaged aesthetics')],
         objeto=r'the raw mean'),

    dict(chave='hasler2003colorfulness',
         titulo=r'\citet{hasler2003colorfulness}',
         papel=r'\textbf{the one autonomous index}, and it indexes colourfulness',
         ops=[('hasler_colorfulness', r'Colourfulness$^{\ddagger}$')],
         objeto=r'the index as published'),
]


# ⛔ estes rotulos DESCREVEM a evidencia encontrada; nao a julgam. «never tests the rule»
# lia como acusacao; «no isolated test of the rule reported» diz o que a leitura achou.
VALIDACAO = {
    'julgamento humano da propriedade': r'\textbf{human ratings of the stated property}',
    'so o resumo': r'summary-level agreement',
    'so o resumo, com ablacao de modulo': r'summary-level agreement, with ablation',
    'nem a regra nem os pesos': r'\textbf{no isolated test of the rule}',
}
SEM_PDF = r'full text unavailable'


def main():
    designA = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
    apur    = json.load(open(QB / 'apuracao_ops.json'))
    alinha  = apur['pares_alinhados_por_construcao']
    autono  = json.load(open(QB / 'quantas_sao_indice_autonomo_na_fonte.json'))
    vasc    = json.load(open(QB / 'o_vascore_do_qaroush_como_a_Eq20_manda.json'))
    korol   = json.load(open(QB / 'o_modulo_do_korolkov_nos_11_segmentos.json'))
    # ⛔ o que a PROPRIA fonte apresenta como evidencia, lido no PDF dela.
    # «nao consta no acervo» nao e «nao validou»: sao linhas diferentes.
    val     = json.load(open(QB / 'o_que_cada_fonte_valida.json'))
    piso    = {x['operacao']: x for x in
               json.load(open(QB / 'o_piso_das_operacoes_isoladas_e_estavel.json'))['por_operacao']}
    # ⛔ SO o lado de sumarizacao: o lado NR-IQA deste arquivo mede contra o Q-Align,
    # nao contra o SIFT implantado, e esta marcado _INUTILIZAVEL na fonte.
    jus     = {x['nome']: x for x in
               json.load(open(QB / 'jusante_lado_a_lado.json'))['linhas']
               if 'sumarizacao' in x['familia']}

    # os dois modulos entram pelo arquivo que os mediu, nao pelo designA
    # ⚠️ o modulo do Korolkov roda em 11 dos 20 segmentos, entao o membro que aparece no
    # MESMO bloco tem de ser o medido nesses mesmos 11. Comparar com o membro da bateria
    # de 20 sugeriria um contraste que ninguem calculou.
    MODULOS = {
        '__VASCORE__': dict(por_tipo=vasc['modulo']['VAScore_soma_crua_Eq20']['por_tipo']),
        '__KOROLKOV__': dict(por_tipo=korol['modulo_por_tipo']),
        '__KOROLKOV_SHARP__': dict(por_tipo=korol['membros']['laplacian_var']['por_tipo']),
    }

    def acuracias(op):
        if op in MODULOS:
            pt = MODULOS[op]['por_tipo']
            vs = [x for x in pt.values() if x is not None]
            return pt, (sum(vs) / len(vs) if vs else None)
        v = designA.get(op)
        if v is None:
            return None, None
        m = dict(zip(v['ordem'], v['acuracia_por_tipo']))
        # ⛔ A MEDIA E SOBRE AS OITO, IGUAL EM TODAS AS LINHAS.
        # Em 08/09 ela saiu por engano na regua «fora os tipos alinhados», que exclui
        # celulas DIFERENTES conforme a operacao: as linhas deixavam de ser comparaveis
        # entre si, que e a unica coisa que uma coluna de media serve para fazer.
        # A versao com exclusao continua existindo, como sensibilidade, no suplementar.
        vals = [a for tp, a in m.items() if a is not None]
        med = sum(vals) / len(vals) if vals else None
        return m, med

    def kap(op):
        v = piso.get(op)
        return None if v is None else v['kappa']

    def keep(op):
        v = jus.get(op)
        return None if v is None else v['pct']

    def num(x, sinal, vermelho_abaixo):
        if x is None:
            return r'\textcolor{black!30}{\tiny n/a}'
        s = ('%+.3f' % x) if sinal else ('%.1f' % x)
        if sinal:
            s = '$%s$' % s
        if vermelho_abaixo is not None and x < vermelho_abaixo:
            return r'\textcolor{accentred}{\textbf{%s}}' % s
        return s

    L = []
    A = L.append
    A(r'%% GERADO por gera_tab_sintese.py. Nao editar a mao.')
    # ⚠️ `[!ht]` prendia a tabela e deixava 6 linhas orfas numa pagina inteira.
    # `[!tbp]` deixa o LaTeX escolher, e o \FloatBarrier garante que ela nao atravesse
    # para dentro da Discussao.
    A(r'\begin{table}[!tbp]')
    A(r'\caption{\textbf{The audit read by source work.} Each band is one source, its role '
      r'for the component, what this bench measured, and what the source itself reports as '
      r'evidence; each row is one component. \emph{Dk} = darkening, \emph{Mo} = motion '
      r'blur, \emph{Bl} = Gaussian blur, \emph{H2} = H.264, \emph{Rs} = rescaling, '
      r'\emph{St} = desaturation, \emph{Ns} = white noise, \emph{Jp} = JPEG: accuracy (per '
      r'cent) on the 800 constructed pairs, green where the operation prefers the '
      r'original and red where it prefers the degraded copy; \textbf{50 is the chance level}. '
      r'\textbf{\emph{Mean} is over all eight types for every row}, so the column compares '
      r'like with like; $^{*}$ marks a degradation acting directly on the quantity the '
      r'operation measures. \emph{Agr}: chance-corrected agreement with LIQE on the '
      r'operational '
      r'clusters. \emph{Kp}: percentage of the 42 representatives also chosen by the '
      r'deployed operation, chance floor 47. The two module rows carry their own sample, '
      r'stated in the band, and the member shown beside a module is measured on that same '
      r'sample. $^{\dagger}$ marks the same statistic used by two works, each row on the '
      r'sample its band states; $^{\ddagger}$ marks one colourfulness computation shown in '
      r'two bands by provenance.}')
    A(r'\label{tab:synthesis}')
    A(r'\centering')
    A(r'\scriptsize')
    A(r'\setlength{\tabcolsep}{2.0pt}')
    A(r'\renewcommand{\arraystretch}{1.05}')
    A(r'\begin{tabular}{@{}l' + 'c' * 8 + r'@{\hskip 5pt}r@{\hskip 5pt}r@{\hskip 4pt}r@{}}')
    A(r'\toprule')
    A(r'& \multicolumn{8}{c}{\textbf{\footnotesize degradation type}} & & &\\')
    A(r'\cmidrule(lr){2-9}')
    A(r'\textbf{Source work / component} & ' + ' & '.join(
        r'\textbf{%s}' % c for c in CABECA)
      + r' & \textbf{Mean} & \textbf{Agr} & \textbf{Kp}\\')
    A(r'\midrule')

    n_linhas = 0
    for t_ in TRABALHOS:
        k = t_['chave']
        if k in val['por_fonte']:
            ev = VALIDACAO[val['por_fonte'][k]['tipo']]
        else:
            ev = SEM_PDF
        A(r'\rowcolor{headerblue!10}\multicolumn{12}{@{}p{\linewidth}@{}}{%s\ '
          r'\textcolor{black!78}{%s;} \textcolor{black!72}{\itshape here: %s;} '
          r'\textcolor{accentblue}{\scriptsize %s}}\\'
          % (t_['titulo'], t_['papel'], t_['objeto'], ev))
        for op, rotulo in t_['ops']:
            por_tipo, media = acuracias(op)
            if por_tipo is None:
                print('  ERRO: sem acuracia medida para %r' % op, file=sys.stderr)
                sys.exit(1)
            al = set(alinha.get(op, []))
            cells = ' & '.join(celula(por_tipo.get(x), x in al) for x in TIPOS)
            med = r'\textbf{%s}' % ('%.1f' % media if media is not None else '--')
            A(r'%s & %s & %s & %s & %s\\' % (
                rotulo, cells, med,
                num(kap(op), True, 0.0), num(keep(op), False, 47.0)))
            n_linhas += 1

    A(r'\bottomrule')
    A(r'\end{tabular}')
    A(r'\end{table}')

    texto = sem_zero('\n'.join(L)) + '\n'
    SAIDA.write_text(texto, encoding='utf-8')
    print('   escrito %s  (%d trabalhos, %d linhas de componente)'
          % (SAIDA.name, len(TRABALHOS), n_linhas))
    print('   autonomas na fonte: %d de %d' % (autono['autonomas'], autono['verificadas']))


if __name__ == '__main__':
    main()
