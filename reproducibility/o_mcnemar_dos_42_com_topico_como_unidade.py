"""⭐⭐ O McNEMAR DOS 42 CLUSTERS RESPEITANDO O TOPICO.

POR QUE EXISTE (12/09/2026, apos parecer de revisor). O corpo compara os dois regimes por
um McNemar exato «over the 42 paired clusters», e o McNemar trata cada par como
observacao independente. ⛔ Os 42 clusters vem de 19 TOPICOS, e a propria Tabela S27 do
suplementar ja declara topico como unidade nos outros dois blocos que usam esses mesmos
42. Entao o artigo aplica duas filosofias de inferencia ao mesmo conjunto de dados.

O QUE ISTO FAZ: refaz o mesmo contraste com a unidade que o desenho implica, pelo mesmo
mecanismo que o artigo ja usa nos 800 pares — troca de sinal EM BLOCO, aqui enumerada
exatamente sobre os 2^19 blocos de topico.

⚠️ PRE-CONDICAO: reproduzir 22/16/12 e o p publicado ANTES de calcular o que e novo. Sem
isso eu nao sei se estou lendo os mesmos dados, e um numero novo plausivel sobre dado
errado e exatamente o modo como cinco valores errados nasceram em 21/08.

⭐ PREVISOES DECLARADAS ANTES DE RODAR:
 1. O p sobe (o bloco so tira independencia, nunca acrescenta).
 2. Continua separando a 0,05, porque 11 contra 1 e desbalanco grande.
 3. Os 12 discordantes NAO estao concentrados num topico so; se estivessem, o teste em
    bloco perderia quase todo o poder e a conclusao cairia.
"""
import json
from itertools import product
from math import comb
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
ART = Path('/home/jader/memoria-agentes/07-Artigos/evaluality-literatura')

c = json.load(open(QB / 'same_frame_same_pooling_control.json'))['clusters']
t = json.load(open(ART / 'third_revision_reanalysis.json'))['same_frame_same_pooling']
assert len(c) == 42 and t['n_clusters'] == 42

completa = set(t['published_change_clusters'])
so_casam = {k for k in c if c[k]['selected']['published_deployed']
            != c[k]['selected']['sift_matched_mean']}
so_scorer = {k for k in c if c[k]['selected']['sift_matched_mean']
             != c[k]['selected']['liqe_matched_mean']}


def mcnemar(A, B):
    b, cc = len(A - B), len(B - A)
    n = b + cc
    if n == 0:
        return b, cc, 1.0
    k = min(b, cc)
    return b, cc, min(1.0, sum(comb(n, i) for i in range(k + 1)) / 2 ** n * 2)


# ---- pre-condicao: reproduzir o publicado -------------------------------------------
pub = {'completa': 22, 'so_scorer': 16, 'so_casam': 12, 'n10': 11, 'n01': 1, 'p': 0.0063}
n10, n01, p_mc = mcnemar(completa, so_casam)
reproduz = (len(completa) == pub['completa'] and len(so_scorer) == pub['so_scorer']
            and len(so_casam) == pub['so_casam'] and n10 == pub['n10']
            and n01 == pub['n01'] and abs(p_mc - pub['p']) < 5e-4)
assert reproduz, ('⛔ NAO reproduzi o publicado: %d/%d/%d, n10=%d n01=%d p=%.4f'
                  % (len(completa), len(so_scorer), len(so_casam), n10, n01, p_mc))

# ---- o mesmo contraste, com o topico como bloco --------------------------------------
topico = {k: k.split('#')[0] for k in c}
TOPICOS = sorted(set(topico.values()))
assert len(TOPICOS) == 19, '⛔ esperava 19 topicos, achei %d' % len(TOPICOS)

# d_t = (discordantes a favor da operacao completa) - (a favor do so-casamento), por topico
d = {}
for k in c:
    if (k in completa) == (k in so_casam):
        continue                      # concordante: o McNemar nao o usa, o bloco tambem nao
    d[topico[k]] = d.get(topico[k], 0) + (1 if k in completa else -1)
D_obs = sum(d.values())
blocos = sorted(d)                    # so topicos que TEM discordante entram na troca
assert D_obs == n10 - n01, '⛔ o desbalanco por topico nao soma o desbalanco global'

extremos = sum(1 for s in product((1, -1), repeat=len(blocos))
               if abs(sum(si * d[b] for si, b in zip(s, blocos))) >= abs(D_obs))
p_bloco = extremos / 2 ** len(blocos)

# ---- quanto o resultado depende de UM topico -----------------------------------------
por_topico = sorted(((tt, v) for tt, v in d.items()), key=lambda x: -abs(x[1]))
sem_o_maior = {k: v for k, v in d.items() if k != por_topico[0][0]}
D_sem = sum(sem_o_maior.values())
bl2 = sorted(sem_o_maior)
p_sem = (sum(1 for s in product((1, -1), repeat=len(bl2))
             if abs(sum(si * d[b] for si, b in zip(s, bl2))) >= abs(D_sem))
         / 2 ** len(bl2)) if bl2 and D_sem else 1.0

out = {
    '_o_que_e': '⭐⭐ O contraste «operacao completa (22) contra so o casamento (12)» '
                'refeito com o TOPICO como unidade, por troca de sinal em bloco enumerada '
                'exatamente. O McNemar publicado trata os 42 clusters como independentes, '
                'e eles vem de 19 topicos.',
    'unidade_de_reamostragem': 'topico de telejornal (bloco de troca de sinal)',
    'pre_condicao_reproduz_o_publicado': {
        'reproduz': reproduz, 'operacao_completa': len(completa),
        'controle_casado_so_o_scorer': len(so_scorer), 'so_o_casamento': len(so_casam),
        'n10': n10, 'n01': n01, 'p_mcnemar_exato': round(p_mc, 4),
        '_leitura': 'confere com o publicado antes de calcular o que e novo',
    },
    'n_clusters': 42, 'n_topicos': 19,
    'COM_O_TOPICO_COMO_UNIDADE': {
        'desbalanco_observado': D_obs,
        'topicos_que_carregam_discordante': len(blocos),
        'atribuicoes_enumeradas': 2 ** len(blocos),
        'p_troca_de_sinal_em_bloco': round(p_bloco, 5),
        'separa_a_005': p_bloco < 0.05,
        'razao_p_bloco_sobre_p_mcnemar': round(p_bloco / p_mc, 2),
    },
    'DEPENDE_DE_UM_TOPICO_SO': {
        'topico_de_maior_peso': por_topico[0][0], 'peso_dele': por_topico[0][1],
        'p_sem_esse_topico': round(p_sem, 5),
        'ainda_separa_sem_ele': p_sem < 0.05,
        'discordantes_por_topico': dict(por_topico),
    },
    'PREVISOES': {
        '1_o_p_sobe': p_bloco > p_mc,
        '2_continua_separando': p_bloco < 0.05,
        '3_nao_esta_num_topico_so': len(blocos) > 1,
    },
    'leitura': ('O desbalanco de %d vem de %d topicos distintos, e a troca de sinal em '
                'bloco devolve p = %.5f contra %.4f do McNemar. A conclusao do corpo '
                '%s com a unidade que o desenho implica.'
                % (D_obs, len(blocos), p_bloco, p_mc,
                   'sobrevive' if p_bloco < 0.05 else 'NAO sobrevive')),
}
json.dump(out, open(QB / 'o_mcnemar_dos_42_com_topico_como_unidade.json', 'w'),
          indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if k != 'DEPENDE_DE_UM_TOPICO_SO'},
                 indent=2, ensure_ascii=False))
print('\nDEPENDE_DE_UM_TOPICO_SO:', json.dumps(out['DEPENDE_DE_UM_TOPICO_SO'],
                                               indent=2, ensure_ascii=False))
