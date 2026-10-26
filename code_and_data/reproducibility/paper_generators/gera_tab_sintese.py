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
import os
import json, re, sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
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
         titulo=r'Ref.~\citep{ke2006highlevel}',
         papel=r'four features of a naive Bayes photo-quality classifier',
         ops=[('ke_edge_distribution', 'Edge distribution'),
              ('ke_hue_count',         'Hue count'),
              ('ke_contraste',         'Contrast'),
              ('ke_colorfulness',      r'Colourfulness$^{\ddagger}$')],
         objeto=r'each feature alone, as a score'),

    dict(chave='srinivas2016rank',
         titulo=r'Ref.~\citep{srinivas2016rank}',
         papel=r'average five attributes into a per-frame quality score',
         ops=[('srinivas_quality', r'The mean rule, our vector')],
         objeto=r'its mean rule, on our attribute vector'),

    dict(chave='qaroush2025diversity',
         titulo=r'Ref.~\citep{qaroush2025diversity}',
         # ⛔ 21/09 (parecer, E75 e TB06): a banda dizia «four terms» e a tabela listava
         # CINCO termos avaliados. O quinto e o `qaroush_ct`, que NAO esta entre as quinze
         # operacoes do inventario: e um diagnostico nosso, e a tabela nao distinguia os
         # dois. Agora o rotulo diz o que ele e, e a contagem da banda fecha com as linhas.
         # ⭐ 27/09 (parecer, checagem da 4.4): o «best term» de 83,1 da Secao 4.4 e o CF da
         # Eq. 20, computado pela formula do Hasler, e a banda NAO o mostrava; nem o MMI. O
         # modulo tem cinco termos (CF + CT + VS + GM + MMI) e agora a banda mostra os cinco.
         papel=r'four audited terms across three objectives, and a five-term attention module',
         ops=[('__VASCORE__',       'Visual-attention module'),
              ('hasler_colorfulness', r'\quad Colourfulness$^{\ddagger}$'),
              ('qaroush_gm',        r'\quad Gradient magnitude'),
              ('qaroush_saliencia', r'\quad Saliency'),
              ('qaroush_ct',        r'\quad Contrast term$^{\S}$'),
              ('__VA_MMI__',        r'\quad Motion magnitude$^{\S}$'),
              ('qaroush_entropia',  'Entropy'),
              ('qaroush_go',        'Gradient orientation')],
         objeto=r'the published rule over the vector implemented here, then each term'),

    dict(chave='korolkov2025keyframe',
         titulo=r'Ref.~\citep{korolkov2025keyframe}',
         papel=r'$0.7\,z(\mathrm{sharp})+0.3\,z(\mathrm{bright})$ as a keyframe score, \textbf{on 11 of the 20 segments}',
         ops=[('__KOROLKOV__',       'The published rule'),
              ('__KOROLKOV_SHARP__', r'\quad Sharpness alone, same 11$^{\dagger}$')],
         objeto=r'the rule, our normalization population'),

    dict(chave='cakmak2025tripss',
         titulo=r'Ref.~\citep{cakmak2025tripss}',
         papel=r'a threshold discarding blurred frames, not a score',
         ops=[('laplacian_var', r'Laplacian variance$^{\dagger}$')],
         objeto=r'the statistic as a scorer, not the filter'),

    dict(chave='jeong2016static',
         titulo=r'Ref.~\citep{jeong2016static}',
         papel=r'a badness term in a cost multiplicative in cluster distance',
         ops=[('contraste_variancia', r'Grey-level dispersion$^{\dagger}$')],
         objeto=r'the term, read increasing'),

    dict(chave='xu2024property',
         titulo=r'Ref.~\citep{xu2024property}',
         papel=r'a discard filter for meaningless frames, and BRISQUE as one of five '
               r'score dimensions',
         # ⭐ 27/09 (parecer, C): a banda dizia «BRISQUE as one of five score
         # dimensions» e so mostrava o filtro. O BRISQUE e justamente o
         # componente que mira fidelidade, que e o construto deste artigo.
         ops=[('contraste_variancia', r'Grey-level dispersion$^{\dagger}$'),
              ('__BRISQUE__', r'\quad BRISQUE, the fidelity dimension$^{\mathrm{m}}$')],
         objeto=r'the filter statistic and the fidelity dimension, read alone'),

    # ⭐ 27/09 (parecer, C): o SIFT+BoVW era a UNICA operacao auditada que nao
    # aparecia na sintese por fonte, embora o corpo diga que ele e auditado «on
    # the same footing». A banda entra, marcada FORA das contagens por banda
    # para nao mexer nas onze fontes: ele e o caso implantado, nao uma das
    # fontes da varredura.
    dict(chave='barbieri2021tese',
         titulo=r'Ref.~\citep{barbieri2021tese}$^{\P}$',
         papel=r'a TF-IDF sum over a visual-word vocabulary, scoring whether a '
               r'segment holds images of interest (a relevance criterion)',
         ops=[('__SIFTBOVW__', r'SIFT$+$BoVW sum$^{\P}$')],
         objeto=r'the score as the source specifies it',
         # ⛔ sem este `ev` a banda caia no SEM_PDF e imprimia «full text
         # unavailable». A tese ESTA no acervo e foi lida; o que ela nao esta e
         # no registro de validacao, que cobre as onze fontes da varredura.
         # Marcador que afirma o que nao se mediu e pior que marcador nenhum.
         ev=r"\textit{the testbed's own operation}"),

    dict(chave='yang2024keyframe',
         titulo=r'Ref.~\citep{yang2024keyframe}',
         papel=r'one texture term of several',
         ops=[('glcm_contraste', 'GLCM contrast')],
         objeto=r'the term alone'),

    dict(chave='huang2024aesthetic',
         titulo=r'Ref.~\citep{huang2024aesthetic}',
         papel=r'one aesthetic attribute of several',
         ops=[('huang_saturacao', 'Saturation')],
         objeto=r'the attribute alone'),

    dict(chave='gygli2014summe',
         titulo=r'Ref.~\citep{gygli2014summe}',
         papel=r'three aesthetic attributes, listed without a combination',
         ops=[('gygli_media_crua', 'Averaged aesthetics')],
         objeto=r'the raw mean'),

    dict(chave='hasler2003colorfulness',
         titulo=r'Ref.~\citep{hasler2003colorfulness}',
         papel=r'\textbf{the one autonomous index}, and it indexes colourfulness',
         ops=[('hasler_colorfulness', r'Colourfulness$^{\ddagger}$')],
         objeto=r'the index as published'),
]


# ⛔ estes rotulos DESCREVEM a evidencia encontrada; nao a julgam. «never tests the rule»
# lia como acusacao; «no isolated test of the rule reported» diz o que a leitura achou.
VALIDACAO = {
    # ⚠️ o objeto que o Ke avalia e o CLASSIFICADOR inteiro, nao cada atributo isolado; as
    # linhas abaixo da banda sao os atributos, e o rotulo generico convidava a leitura errada.
    # ⚠️ 13/09: dizia «at the level of the whole» e para o Ke isso e FALSO. A Fig. 8 dele
    # traz «Individual and combined results for each of our quality metrics». O rotulo
    # generico servia ao Hasler e mentia sobre o Ke, entao agora ha um para cada.
    'julgamento humano da propriedade': r'\textbf{human ratings of the named property}',
    'julgamento humano, por atributo e combinado':
        r'\textbf{human ratings; per feature and combined}',
    'so o resumo': r'summary-level evaluation',
    'so o resumo, com ablacao de modulo': r'summary-level evaluation, with ablation',
    'so o resumo, com ablacao de etapa':
        r'summary-level evaluation, with an optimisation ablation',
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
    _jl = json.load(open(QB / 'jusante_lado_a_lado.json'))
    jus     = {x['nome']: x for x in _jl['linhas'] if 'sumarizacao' in x['familia']}
    # ⛔ 22/09 (parecer v4, 2.5): sete operacoes saiam aqui como «n/a», que a legenda define
    # como teste NAO APLICAVEL — mas a Figura S4 mostra a retencao delas. O `n/a` estava
    # dizendo «nao medido neste arquivo», que e outra coisa. A figura ja complementa com o
    # caminho publicado; a tabela passa a ler a MESMA fonte, com o mesmo controle de
    # populacao, para as duas pecas nao discordarem sobre a mesma celula.
    for _n, _v in json.load(open(
            QB / 'jusante_ops_faltantes_caminho_velho.json'))['concordancia_com_sift'].items():
        if _n not in jus:
            jus[_n] = {'nome': _n, 'pct': _v['pct'], 'n': _v['n']}
    assert all(v['n'] == _jl['n_clusters'] for v in jus.values()), \
        '⛔ populacao diferente entre operacoes na coluna de retencao'

    # os dois modulos entram pelo arquivo que os mediu, nao pelo designA
    # ⚠️ o modulo do Korolkov roda em 11 dos 20 segmentos, entao o membro que aparece no
    # MESMO bloco tem de ser o medido nesses mesmos 11. Comparar com o membro da bateria
    # de 20 sugeriria um contraste que ninguem calculou.
    # ⭐ o SIFT+BoVW e o BRISQUE nao estao no designA (nao sao operacoes da
    # varredura): a degradacao dos dois vem da TABELA_FINAL, medida nos MESMOS
    # 800 pares e com os mesmos oito tipos.
    _tf = {l['nome']: l for l in json.load(open(QB / 'TABELA_FINAL.json'))['linhas']}
    MODULOS = {
        '__SIFTBOVW__': dict(por_tipo=_tf['SIFT+BoVW']['acc']),
        '__BRISQUE__': dict(por_tipo=_tf['brisque']['acc']),
        '__VASCORE__': dict(por_tipo=vasc['modulo']['VAScore_soma_crua_Eq20']['por_tipo']),
        '__VA_MMI__': dict(por_tipo=vasc['membros']['qaroush_mmi']['por_tipo']),
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

    # ⛔ 22/09 (parecer v6, 4.3): o `n/a` da legenda quer dizer «nao se aplica». Para o
    # termo de contraste a concordancia APLICA e so nao foi calculada, e o simbolo
    # certo e o traco. Sem esta excecao a tabela representa mal a propria ausencia.
    # ⭐ 27/09, SEGUNDA PASSADA: o Agr do BRISQUE contra o LIQE EXISTE, e eu
    # tinha parado cedo demais. Ele esta em `piso_as_duas_familias.json`, que e
    # a fonte da propria afirmacao da 4.5 -- os agregados publicados batem com
    # ele exatamente (n=10, passam=10, mediana .7078, maximo .7753).
    # ⚠️ Os dois arquivos que NAO servem, para nao serem tentados de novo:
    #   - `jusante_lado_a_lado.json` se marca `_INUTILIZAVEL`: ali a referencia
    #     e o Q-ALIGN, nao o LIQE.
    #   - `o_contraste_das_familias_por_referencia.json` da -0.618 porque NAO
    #     ALINHA POLARIDADE: os unicos negativos da lista dele sao o BRISQUE e
    #     o NIQE, exatamente os dois modelos menor-e-melhor da Tabela 2.
    # ⚠️ E FICA DECLARADO que a procedencia difere da das operacoes: as linhas
    # de operacao vem de `o_piso_das_operacoes_isoladas_e_estavel.json`, e os
    # dois arquivos discordam em 7 das 10 operacoes que compartilham, por 0,04
    # a 0,09. E pouco ao lado do contraste que a tabela mostra (.685 contra uma
    # mediana de .281), mas nao e a mesma conta, e o marcador na legenda diz
    # de onde a celula do modelo vem.
    _duas = json.load(open(QB / 'piso_as_duas_familias.json'))['por_metodo']
    assert _duas['brisque']['familia'] == 'NR-IQA' and _duas['brisque']['n_clusters'] == 42, \
        '⛔ o registro do BRISQUE mudou de familia ou de populacao'
    KAPPA_MODELO = {'__BRISQUE__': _duas['brisque']['kappa_uniform']}
    NAO_RODADO = {'qaroush_ct', '__VA_MMI__'}
    # ⭐ o do SIFT+BoVW existe, e no regime CERTO: e o mesmo `liqe_x_implantada`
    # que a 4.5 passou a reportar depois do parecer.
    _sub = json.load(open(QB / 'a_substituicao_concorda_acima_do_acaso.json'))
    KAPPA_EXTRA = {'__SIFTBOVW__':
                   _sub['por_linha']['liqe_x_implantada']['kappa_contra_o_acaso']}

    def kap(op):
        if op in KAPPA_MODELO:
            return KAPPA_MODELO[op]
        if op in KAPPA_EXTRA:
            return KAPPA_EXTRA[op]
        v = piso.get(op)
        if v is None and op in NAO_RODADO:
            return 'TRACO'
        return None if v is None else v['kappa']

    def keep(op):
        v = jus.get(op)
        return None if v is None else v['pct']

    def num(x, sinal, vermelho_abaixo):
        if x == 'TRACO':
            return r'\textcolor{black!30}{---}'
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
    A(r'\begin{table}[p]')
    # ⭐ 21/09: legenda ENXUTA (criterio 30 e TB06). A anterior tinha 214 palavras.
    # ⛔ 22/09 (parecer v2, V2-081): a legenda anunciava 800 pares para a tabela inteira,
    # enquanto a faixa do Korolkov roda em 11 segmentos; e Agr, Kp, *, †, ‡ e § apareciam
    # sem definicao. Cada coluna, simbolo e denominador fica declarado aqui.
    A(r'\caption{\textbf{The audit read by source work.} Each band is one source with the '
      r'role it declares; each row is one component. \textbf{Degradation columns} give '
      r'strict accuracy (per cent) on the constructed pairs, \textbf{50 being chance}, '
      r'green where the operation prefers the original and red where it prefers the '
      r'degraded copy; every cell prints its value, so the table reads in '
      r'greyscale. \emph{Dk} darkening, \emph{Mo} motion blur, \emph{Bl} Gaussian blur, '
      r'\emph{H2} H.264, \emph{Rs} rescaling, \emph{St} desaturation, \emph{Ns} white '
      r'noise, \emph{Jp} JPEG. \textbf{Mean} is over all eight types, not the '
      r'seven-type contrast of Section~\ref{sec:combinations}. \textbf{Agr} is '
      r'chance-corrected agreement with LIQE, the designated reference for the '
      r'literature-derived operations, over the 42 operational clusters. '
      r'\textbf{Denominator}: 800 pairs (20 segments $\times$ 8 types $\times$ 5 levels), '
      r'except the Ref.~\citep{korolkov2025keyframe} band, which runs on the 11 segments '
      r'carrying both of its inputs and therefore on 440 pairs. '
      r'$^{*}$ the degradation acts directly on the quantity that operation measures; '
      r'$^{\dagger}$ the same computation is used by two source works, so the two rows are '
      r'not independent evidence; $^{\ddagger}$ the same Hasler expression, named by '
      r'several sources; $^{\S}$ a term of the published module implemented after the '
      r'inventory freeze, outside the counts each band states; $^{\P}$ audited on the '
      r'same footing but outside the '
      r"eleven-work count, because it is the testbed's own operation. "
      r'$^{\mathrm{m}}$ the one model row: its agreement comes from the '
      r'common-reference analysis of Section~\ref{sec:screen_results}, which scores both '
      r'families against LIQE. \emph{n/a} marks a test that does not apply, and '
      r'\textbf{a dash marks one that applies but was not run}.' + '}')
    A(r'\label{tab:synthesis}')
    A(r'\centering')
    A(r'\tiny')  # 27/09: \scriptsize nao cabia mais na pagina
    A(r'\setlength{\tabcolsep}{2.0pt}')
    A(r'\renewcommand{\arraystretch}{0.86}')  # 27/09: com \tiny, 0,95 ainda passava
    A(r'\begin{tabular}{@{}l' + 'c' * 8 + r'@{\hskip 4pt}r@{\hskip 4pt}r@{}}')
    A(r'\toprule')
    A(r'& \multicolumn{8}{c}{\textbf{\footnotesize degradation type}} & &\\')
    A(r'\cmidrule(lr){2-9}')
    A(r'\textbf{Source work / component} & ' + ' & '.join(
        r'\textbf{%s}' % c for c in CABECA)
      + r' & \textbf{Mean} & \textbf{Agr}\\')
    A(r'\midrule')

    n_linhas = 0
    for t_ in TRABALHOS:
        k = t_['chave']
        if k in val['por_fonte']:
            _tipo = val['por_fonte'][k]['tipo']
            if k == 'ke2006highlevel' and _tipo == 'julgamento humano da propriedade':
                _tipo = 'julgamento humano, por atributo e combinado'
            ev = VALIDACAO[_tipo]
        elif t_.get('ev'):
            ev = t_['ev']
        else:
            ev = SEM_PDF
        A(r'\rowcolor{headerblue!10}\multicolumn{11}{@{}p{\linewidth}@{}}{%s\ '
          r'\textcolor{black!78}{%s;} \textcolor{black!72}{\itshape here: %s;} '
          # ⚠️ 21/09: era `\scriptsize` FIXO. Quando o corpo da tabela desceu para
          #    `\tiny`, o rotulo ficou MAIOR que os dados e passou a competir com
          #    eles. Sem comando de tamanho ele herda o da tabela, que e o certo.
          r'\textcolor{accentblue}{%s}}\\'
          % (t_['titulo'], t_['papel'], t_['objeto'], ev))
        for op, rotulo in t_['ops']:
            por_tipo, media = acuracias(op)
            if por_tipo is None:
                print('  ERRO: sem acuracia medida para %r' % op, file=sys.stderr)
                sys.exit(1)
            al = set(alinha.get(op, []))
            cells = ' & '.join(celula(por_tipo.get(x), x in al) for x in TIPOS)
            med = r'\textbf{%s}' % ('%.1f' % media if media is not None else '--')
            A(r'%s & %s & %s & %s\\' % (
                rotulo, cells, med, num(kap(op), True, 0.0)))
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
