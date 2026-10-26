#!/usr/bin/env python3
"""A TABELA TAXONOMICA: que classe de metodo de qualidade visual cada sumarizador usa,
e quais classes o testbed instancia.

As quatro classes vieram do [co-author], por e-mail de 21/09/2026. ⚠️ 28/09
(cli-3, corrigido a pedido do [author]): este comentario dizia que «a tabela diz isso», e nao
diz, nem deve: o [co-author] e orientador e COAUTOR, entao a taxonomia e dos autores do artigo e
nao ha credito a terceiro a declarar na legenda. Nao acrescentar o nome dele ao texto.

Duas tabelas, porque as duas perguntas dele sao diferentes e cabem em lugares diferentes:

  `tab_taxonomia.tex`             CORPO. Quatro linhas, uma por classe: quantos trabalhos
                                  da literatura a usam, quantas operacoes o testbed
                                  instancia nela, e o veredito da bancada.
  `tab_taxonomia_por_trabalho.tex` SUPLEMENTAR. Um trabalho por linha, marcando as classes
                                  que ele usa. E a tabela que o e-mail pede literalmente,
                                  e ela nao cabe no corpo.

⚠️ AS DUAS COLUNAS DA TABELA DO CORPO NAO TEM O MESMO ESTATUTO, e a legenda diz isso:
  - «trabalhos» vem de varredura por termo, com precisao MEDIDA de 0,63. E RASTREIO.
  - «operacoes» vem do inventario, conferido fonte a fonte. E FIRME.
Somar as duas numa leitura unica seria tratar triagem como medicao.
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from caminho_dos_dados import DADOS as QB   # noqa: E402
from gera_tab_sintese import TRABALHOS       # noqa: E402

# ⭐ 27/09 (parecer, item 1): a tabela so dava CONTAGENS, e o pedido do [co-author] era a
# taxonomia TRABALHOS x CLASSES. A coluna nova sai das bandas da Tabela 6 (mesma lista, nao
# digitada): cada banda conta na classe 1, salvo as operacoes marcadas abaixo.
#   `__BRISQUE__`  -> classe 3 (o [59] usa um modelo dedicado como dimensao de fidelidade)
#   `__SIFTBOVW__` -> classe 2 (a operacao do proprio testbed)
# ⭐ E a classe 4 TEM fonte auditada: o Jeong [27], Eq. 11, soma a distancia de Mahalanobis
# de cada quadro ao centro do seu cluster aos termos de qualidade, «an additional measure of
# image quality» (PDF, p. 5, conferido em 27/09). O testbed a instancia sobre DINOv2.
CLASSE_DA_OP = {'__BRISQUE__': 'C3', '__SIFTBOVW__': 'C2'}
FONTE_C4 = ['jeong2016static']


def fontes_por_classe():
    por = {c: [] for c in ('C1', 'C2', 'C3', 'C4')}
    for t in TRABALHOS:
        for op, _ in t['ops']:
            c = CLASSE_DA_OP.get(op, 'C1')
            if t['chave'] not in por[c]:
                por[c].append(t['chave'])
    por['C4'] += [k for k in FONTE_C4 if k not in por['C4']]
    return por

CORPO = AQUI / 'tab_taxonomia.tex'
SUPL = AQUI / 'tab_taxonomia_por_trabalho.tex'

CURTO = {
    # ⭐ 28/09 (parecer): nomes curtos; os longos quebravam em tres linhas na coluna.
    'C1': 'Low-level pixel heuristics',
    'C2': 'Visual-word counting',
    # ⛔ 21/09 (parecer, TB01, criterios 7, 8, 10, 14, 29, 30, 35): o rotulo dizia
    # «classical statistical» e a linha recebia DEZ modelos — CNNs, transformers e
    # modelos visao-linguagem, que nao sao estatisticos classicos. O nome da classe passa
    # a ser o que a classe E (modelos DEDICADOS a medir qualidade), e a subfamilia fica
    # na coluna de representantes, onde se pode conferir.
    'C3': 'Dedicated NR-IQA models',
    'C4': 'Deep representativeness proxies',
}

EXEMPLO = {
    'C1': 'Laplacian variance, colourfulness',
    # ⛔ 27/09 (parecer): «SIFT+BoVW with TF-IDF (the SIFT+BoVW operation)» era
    # tautologico -- a celula se explicava por si mesma. A fonte e o que faltava.
    'C2': 'SIFT+BoVW with TF-IDF',
    'C3': 'BRISQUE, NIQE, LIQE, MUSIQ',
    'C4': 'Distance to cluster centroid',
}


# ⛔ 21/09: o acervo e ALVO MOVEL, e a tabela publicava a contagem sem data. O
# `taxonomia_das_classes.json` varre a pasta viva (`library/papers`) e registrou 212;
# no mesmo dia, a tarde, outro trabalho acrescentou 22 PDFs e a pasta foi para 234. O
# snapshot fica pinado por conteudo no `por_pdf` do proprio JSON (212 entradas nomeadas),
# e a DATA passa a ir na legenda, pela mesma convencao do `gera_tab_protocolo.py`. ⚠️ Sem
# isto, este 212 e o 186 do protocolo parecem duas contagens do mesmo acervo que nao
# fecham, quando sao duas VARREDURAS do acervo em datas diferentes.
#
# ⛔ E a DATA SOZINHA NAO BASTA, aviso do `@agente-iqa-cli-3`: no dia 21/09 houve DUAS
# contagens, 212 de manha e 234 as 16h07, depois de 22 aquisicoes. Um leitor do [venue] nao
# recontaria por hora, entao a legenda fecha a ambiguidade pelo outro lado: aponta para o
# SNAPSHOT LIBERADO com o artigo, que a `guarda_arquivo_publicado` ja obriga a estar no
# pacote, e cuja lista de 212 nomes e o que se reconta. A pasta viva nao e a referencia.
# 📄 as quatro contagens datadas com hora: `MAPEAMENTO-SISTEMATICO.md` §4.1 (memoria).
DATA_VARREDURA = '21 September 2026'


def _tex(s):
    return s.replace('&', r'\&').replace('_', r'\_')


def main():
    d = json.load(open(QB / 'classes_contra_o_testbed.json'))
    tx = json.load(open(QB / 'taxonomia_das_classes.json'))
    linhas = d['por_classe']
    n_sum = d['n_sumarizadores']
    n_pdf = d['n_pdfs_no_acervo']

    # ---------------- tabela do corpo ----------------
    # ⭐ 28/09 (parecer): a legenda era maior que a tabela, com ressalvas aninhadas, e as
    # colunas estreitas quebravam cabecalho, nome de classe e a lista de onze citacoes.
    # Legenda: o que cada coluna e, uma vez. A frase da classe 4 foi para a 4.1.
    L = [r'\begin{table}[!ht]', r'\centering',
         r'\caption{\textbf{Four classes of scoring method for the quality criterion.} '
         r'\emph{Ops}: operations instantiated in this testbed. \emph{Papers}: of the %d '
         r'summarization papers in the archive, those in which a term sweep finds the '
         r'technique mentioned, not its use as a quality score (triage, not confirmed '
         r'adoption; Table~S31). \emph{Sources}: works whose operations are audited '
         r'(Table~\ref{tab:synthesis}). SIFT: scale-invariant feature transform; BoVW: bag '
         r'of visual words; TF-IDF: term frequency--inverse document frequency.' % n_sum + '}',
         r'\label{tab:taxonomy}', r'\small',
         r'\renewcommand{\arraystretch}{1.15}',
         # ⚠️ tabular* com \extracolsep{\fill} deixava buracos brancos entre as celulas
         # coloridas do cabecalho e das faixas; larguras fixas somam a largura do texto.
         r'\setlength{\tabcolsep}{5pt}',
         r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.6cm}rr'
         r'>{\raggedright\arraybackslash}p{2.9cm}'
         r'>{\raggedright\arraybackslash}p{3.1cm}@{}}', r'\toprule',
         r'\rowcolor{headerblue}',
         r'\hd{Class} & \hd{Ops} & \hd{Papers} & \hd{Sources} & \hd{Example here} \\',
         r'\midrule']
    fontes = fontes_por_classe()
    for i, c in enumerate(['C1', 'C2', 'C3', 'C4']):
        v = linhas[c]
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        if len(fontes[c]) > 3:
            cit = r'%d works (Table~\ref{tab:synthesis})' % len(fontes[c])
        else:
            cit = r'\citep{%s}' % ','.join(fontes[c]) if fontes[c] else 'none'
        L.append(f'{cor}{_tex(CURTO[c])} & '
                 f'{v["operacoes_instanciadas_no_testbed"]} & '
                 f'{v["trabalhos_na_literatura"]} & {cit} & {_tex(EXEMPLO[c])} \\\\')
    L += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    CORPO.write_text('\n'.join(L) + '\n', encoding='utf-8')

    # ---------------- tabela do suplementar ----------------
    CH = {'C1': 'C1_heuristicas_de_baixo_nivel', 'C2': 'C2_bovw_e_contagem_artesanal',
          'C3': 'C3_nriqa_estatistico_classico',
          'C4': 'C4_proxy_profundo_de_selecao'}
    FIRME = {'centroide', 'representatividade', 'representativid'}
    sm = {k: v for k, v in tx['por_pdf'].items() if v['e_sumarizador']}

    def marca(v, c):
        hits = v['classes'].get(CH[c], [])
        if c == 'C4':
            # ⛔ so conta a perna que nomeia SELECAO. O termo `cosseno` casa tambem com
            # redundancia e agrupamento, que nao e escore de qualidade.
            hits = [h for h in hits if h in FIRME]
        return r'$\bullet$' if hits else ''

    ordenado = sorted(sm.items(),
                      key=lambda kv: (-sum(1 for c in CH if marca(kv[1], c)), kv[0]))
    S = [r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{6.0cm} cccc@{}}',
         r'\caption{\textbf{Class-term matches in the curated summarization archive.} '
         r'It lists, work by work, which class terms the sweep found. '
         r'A marker '
         r'means the term sweep found the class in the body of the paper, with the '
         r'bibliography removed. \textbf{This is triage, not a verdict}: a marker is a '
         r'candidate for reading rather than a claim about the work. The term sweep is '
         r'an automated retrieval check over an archive assembled during the thesis '
         r'research; it is not a systematic mapping, and a match implies no reading of '
         r'the matched work. The precision '
         r'measured for the archive sweep recorded in Table~\ref{tab:protocolo} was measured on a '
         r'different term set and is not claimed for this sweep. Class~4 is marked only when the text names the '
         r'selection use, distance to a cluster centre or representativeness; cosine '
         r'similarity alone is not counted, because in summarization it serves redundancy '
         r'and clustering far more often than quality.' + '}\\\\',
         r'\label{tab:taxonomy_works}\\',
         r'\toprule', r'\rowcolor{headerblue}',
         r'\hd{Work} & \hd{C1} & \hd{C2} & \hd{C3} & \hd{C4} \\', r'\midrule',
         r'\endfirsthead', r'\toprule', r'\rowcolor{headerblue}',
         r'\hd{Work} & \hd{C1} & \hd{C2} & \hd{C3} & \hd{C4} \\', r'\midrule',
         r'\endhead', r'\bottomrule', r'\endfoot']
    for i, (nome, v) in enumerate(ordenado):
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        base = nome.replace('.pdf', '')
        S.append(f'{cor}\\cite{{{base}}} & ' +
                 ' & '.join(marca(v, c) for c in ('C1', 'C2', 'C3', 'C4')) + r' \\')
    S.append(r'\end{longtable}')
    SUPL.write_text('\n'.join(S) + '\n', encoding='utf-8')

    print(f'  corpo: 4 classes -> {CORPO.name}')
    print(f'  suplementar: {len(ordenado)} trabalhos -> {SUPL.name}')
    for c in ('C1', 'C2', 'C3', 'C4'):
        v = linhas[c]
        print(f'    {c}  literatura {v["trabalhos_na_literatura"]:>3}   '
              f'testbed {v["operacoes_instanciadas_no_testbed"]:>3}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
