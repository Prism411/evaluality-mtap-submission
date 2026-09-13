"""⭐⭐ A COLUNA `Mean` DA TABELA S9 REPRODUZ A FONTE QUE SUSTENTA A S7?

POR QUE EXISTE (13/09/2026). A S7 imprime QualiCLIP 10/15 e a coluna `Mean` da S9 imprime
9/15, as duas anunciando top-1 agreement com a referencia nos MESMOS 15 clusters. A S7 tem
produtor declarado no manifesto (`indomain_bovw.py` / `e2e_analyse.py` -> `indep13.json`);
a S9 NAO tem produtor apontavel.

⚠️ O `@agente-iqa-cli-3` fez a distincao que decide a acao, e ela e medivel:
  «uma celula que diverge numa tabela que reproduz no resto nao e a mesma coisa que uma
   tabela sem produtor. A primeira e suspeita localizada; a segunda e ausencia de
   verificabilidade.»

⭐⭐ A ORDEM DA EVIDENCIA IMPORTA, e ela e dele tambem: o argumento de MECANISMO vem antes
do p, e nao depende de nulo nenhum. As tres linhas nao batem «em alguma coisa»: batem nos
valores ESPECIFICOS 11, 10 e 10 do `indep13.json`. Se for a mesma grandeza computada da
mesma fonte nos mesmos clusters, elas TEM de bater, e nao ha probabilidade envolvida. O p
responde «pode ser acaso?»; o mecanismo responde «e a mesma conta?». Um revisor que nao
aceite o nulo ainda tem o mecanismo de pe.

⛔ E A PRIMEIRA VERSAO DESTE ARQUIVO REPORTAVA p = 0,00708, QUE ERA OTIMISTA. O nulo era
uniforme dentro do suporte: apertava um lado (so os valores que a fonte usa) e afrouxava o
outro (uniformidade dentro dele). ⚠️ Achado pelo `@agente-iqa-cli-3`, e na direcao de
ENFRAQUECER o numero. Medida a frequencia real, cada linha tem 3/15 de chance de bater, nao
1/8, e o p sobe para 0,0272. O veredito nao muda; a folga sim.

⛔ O QUE ISTO NAO FAZ: nao decide o valor da celula. Decidir exigiria o produtor da S9, que
nao existe. Decide apenas QUAL DAS DUAS SITUACOES e a do artigo.
"""
import json
import re
from collections import Counter
from itertools import product
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
ART = Path('/home/jader/memoria-agentes/07-Artigos/evaluality-literatura')

# ---- a coluna `Mean` da S9, lida do suplementar ---------------------------------------
t = (ART / 'supplementary.tex').read_text(errors='replace')
i = t.find('label{tab:pooling}')
bloco = t[i:t.find('bottomrule', i)]
S9 = {}
for l in bloco.split('\n'):
    if '&' not in l:
        continue
    cels = [c.strip() for c in l.split('&')]
    nome = re.sub(r'\\rowcolor\{\w+\}|\\textbf\{|\}', '', cels[0]).strip()
    if nome in ('LIQE', 'NIQE', 'QualiCLIP', 'BRISQUE'):
        m = re.search(r'(\d+)/15', cels[1])
        if m:
            S9[nome] = int(m.group(1))
assert len(S9) == 4, '⛔ nao li as quatro linhas da S9: %r' % S9

# ---- a fonte que sustenta a S7 ---------------------------------------------------------
FONTE = json.loads((ART / 'indep13.json').read_text())['all15']['rows']
S7 = {k: v['agree'] for k, v in FONTE.items()}
assert all(k in S7 for k in S9), '⛔ a fonte nao cobre os quatro metodos da S9'

batem = {k: S9[k] for k in S9 if S9[k] == S7[k]}
divergem = {k: {'S9_mean': S9[k], 'fonte_da_S7': S7[k]} for k in S9 if S9[k] != S7[k]}
n_bate = len(batem)

# ---- o nulo EMPIRICO: sortear da distribuicao que a propria fonte tem -------------------
vals = list(S7.values())
freq = Counter(vals)
# ⚠️ A CHANCE E DE COINCIDIR COM O VALOR DA FONTE, nao com o que a S9 imprime. Para o
# QualiCLIP isso e freq(10) e nao freq(9): o valor 9 que a S9 traz e o resultado observado,
# nao o alvo. `freq(9)` vale 1/15 e NAO entra na conta. ⛔ Vale dito porque um leitor ja
# tropecou aqui: a estatistica e «quantas linhas da S9 coincidem com a S7», e sob o nulo a
# S9 sorteia um valor cuja chance de cair em S7[k] e freq(S7[k]).
#
# 📌 E POR ISSO os quatro p saem iguais a 0,20: a fonte vale 11, 10, 10, 10 para estes
# quatro metodos, e freq(11) = freq(10) = 3 de 15. Entao a Poisson-binomial abaixo, que e
# o caso geral com p por linha, DEGENERA aqui na binomial C(4,3)p³(1-p) + p⁴. O codigo faz
# o caso geral de proposito: se a fonte mudar, os p deixam de coincidir e a conta continua
# certa sem ninguem reescrever.  ⚠️ Nome corrigido apos observacao do @agente-iqa-cli-3.
p_linha = {k: freq[S7[k]] / len(vals) for k in S9}
# Poisson-binomial exata sobre os 2^4 subconjuntos
nomes = sorted(S9)
p_emp = sum(
    prod for sub in product([0, 1], repeat=len(nomes))
    if sum(sub) >= n_bate
    for prod in [eval('*'.join(
        str(p_linha[k]) if b else str(1 - p_linha[k]) for k, b in zip(nomes, sub)))]
)

# ---- o nulo uniforme, mantido e rotulado como OTIMISTA ---------------------------------
suporte = sorted(set(vals))
casos = list(product(suporte, repeat=len(S9)))
p_unif = sum(1 for c in casos
             if sum(1 for v, k in zip(c, nomes) if v == S7[k]) >= n_bate) / len(casos)

out = {
    '_o_que_e': '⭐⭐ A coluna `Mean` da Tabela S9 conferida contra a fonte que sustenta a '
                'S7, para separar «suspeita localizada» de «tabela sem verificabilidade».',
    'unidade_de_reamostragem': 'metodo (linha da S9)',
    'fonte_da_S7': 'indep13.json, all15.rows (produtor declarado no reproducibility_manifest)',
    'a_S9_tem_produtor': False,
    '_por_que': 'o unico JSON dos quatro agrupamentos temporais declara ser a versao '
                'aplicada as OPERACOES nos 42 clusters, e diz que a S9 faz isso para '
                'quatro MODELOS em 15 clusters. Nao e a fonte dela.',

    '1_MECANISMO_nao_depende_de_nulo': {
        '_leitura': 'as tres linhas nao batem «em alguma coisa»: batem nos valores '
                    'ESPECIFICOS da fonte. Se for a mesma grandeza computada da mesma '
                    'fonte nos mesmos clusters, elas TEM de bater, e nao ha probabilidade '
                    'envolvida. Este e o argumento mais dificil de contestar.',
        'reproduzem_o_valor_exato': batem,
        'DIVERGE': divergem,
        'quantas_de_quantas': '%d de %d' % (n_bate, len(S9)),
    },

    '2_p_como_confirmacao_de_que_nao_e_acaso': {
        'NULO_EMPIRICO_principal': {
            'como': 'cada linha sorteada da distribuicao que a propria fonte tem. A chance '
                    'e de COINCIDIR COM O VALOR DA FONTE, nao com o que a S9 imprime: para '
                    'o QualiCLIP e freq(10) e nao freq(9), e freq(9)=1/15 nao entra.',
            'a_conta': 'Poisson-binomial (caso geral, p por linha). Aqui os quatro p saem '
                       'iguais a 0,20 porque a fonte vale 11,10,10,10 e freq(11)=freq(10)=3 '
                       'de 15, entao ela DEGENERA na binomial C(4,3)p^3(1-p)+p^4. O codigo '
                       'faz o caso geral para continuar certo se a fonte mudar.',
            'frequencias_na_fonte': dict(sorted(freq.items())),
            'p_de_bater_por_linha': {k: round(v, 4) for k, v in p_linha.items()},
            'p_de_bater_em_%d_ou_mais' % n_bate: round(p_emp, 5),
        },
        'NULO_UNIFORME_otimista': {
            'como': 'valores uniformes no suporte %s. ⛔ Aperta um lado (so o suporte da '
                    'fonte) e AFROUXA o outro (uniformidade dentro dele)' % suporte,
            'p_de_bater_em_%d_ou_mais' % n_bate: round(p_unif, 5),
            '_por_que_nao_e_o_principal': 'reportado na primeira versao deste arquivo como '
                                          'se fosse conservador, e nao era. Achado pelo '
                                          '@agente-iqa-cli-3, na direcao de enfraquecer.',
        },
        'razao_entre_os_dois': round(p_emp / p_unif, 2),
    },

    'VEREDITO': ('suspeita localizada' if n_bate >= 3 and p_emp < 0.05
                 else 'nao separa das duas situacoes'),
    'leitura': ('A coluna reproduz os valores EXATOS da fonte em %d das %d linhas, o que e '
                'identidade e nao coincidencia; sob o nulo empirico isso tem p = %.4f '
                '(o nulo uniforme daria %.5f, e era otimista). A coluna E verificavel '
                'contra a fonte da S7; o que nao se verifica e UMA celula. ⛔ Isto NAO '
                'decide o valor dela: decidir exigiria o produtor da S9.'
                % (n_bate, len(S9), p_emp, p_unif)),
}
json.dump(out, open(QB / 'a_coluna_mean_da_S9_reproduz_a_S7.json', 'w'),
          indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
