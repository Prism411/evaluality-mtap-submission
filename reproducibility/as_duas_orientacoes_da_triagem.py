"""⛔⛔ AS DUAS FAMILIAS SAO TRIADAS SOB ORIENTACOES DIFERENTES, E ISSO NAO ESTAVA DITO.

POR QUE EXISTE (13/09/2026, terceiro parecer). O revisor mostrou que a explicacao que eu
tinha posto na legenda da S30 («reportada sem alinhamento») NAO fecha: colourfulness e
laplacian invertem de sinal entre S18 e S30, mas edge distribution (+.298), saliency (+.075)
e spatial information (+.251) aparecem IGUAIS nas duas. Uma unica convenção «alinhado x nao
alinhado» nao produz esse padrao.

⭐ A CAUSA, lida no gerador (`as_combinacoes_COMO_A_LITERATURA_PUBLICA.py:99`):

    al = -por_tipo if np.nanmean(por_tipo) < 0 else por_tipo

A S30 orienta pelo SINAL DA MEDIA DOS PROPRIOS DADOS; a S18 orienta pela DIRECAO QUE A
FONTE DECLARA. Onde as duas coincidem, o valor e o mesmo; onde a fonte declara o contrario
do que os dados mostram, os sinais divergem. Isso explica as cinco linhas.

📌 POR QUE A ORIENTACAO E OUTRA, e nao e descuido: uma COMBINACAO de atributos nao tem
direcao declarada por fonte nenhuma. A fonte declara direcao para o atributo, nao para o
z-score de tres deles somados. Entao a S30 nao tinha como usar a regra da S18.

⭐⭐ MAS ISSO TEM UMA CONSEQUENCIA QUE PRECISA SER DITA, e ela e favoravel:
|rho| >= rho_alinhado sempre. A porta dos compostos e portanto MAIS PERMISSIVA que a das
operacoes. Nenhum composto passa nem assim, o que torna a conclusao CONSERVADORA e nao
otimista.

⛔ O que isto NAO faz: nao refaz a triagem. Documenta qual orientacao cada familia usa e
mede a direcao da diferenca.
"""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
ART = Path('/home/jader/memoria-agentes/07-Artigos/evaluality-literatura')

comb = json.loads((QB / 'as_combinacoes_COMO_A_LITERATURA_PUBLICA.json').read_text())
ops = json.loads((QB / 'as_15_na_regra_do_artigo.json').read_text())['por_operacao']

# as combinacoes de UM termo so sao o par direto: mesma quantidade, duas orientacoes
pares = []
for c in comb['por_combinacao']:
    if len(c['campos']) != 1:
        continue
    k = c['campos'][0]
    if k not in ops:
        continue
    s18 = ops[k]['sensibilidade_media']
    s30 = c['media_z']['mean_rho']
    pares.append({'operacao': k, 'S18_alinhada_pela_fonte': s18,
                  'S30_orientada_pelos_dados': s30,
                  'mesma_magnitude': abs(abs(s18) - abs(s30)) < 5e-4,
                  'sinal_inverte': (s18 < 0) != (s30 < 0)})
assert pares, '⛔ nenhum par direto: a comparacao nao se monta'

invertem = [p['operacao'] for p in pares if p['sinal_inverte']]
iguais = [p['operacao'] for p in pares if not p['sinal_inverte']]
magnitude_bate = all(p['mesma_magnitude'] for p in pares)

out = {
    '_o_que_e': '⛔⛔ As duas familias da triagem usam ORIENTACOES diferentes: a S18 alinha '
                'pela direcao que a fonte declara e a S30 pelo sinal da media dos proprios '
                'dados. Isso explica por que algumas operacoes unitarias invertem de sinal '
                'entre as duas tabelas e outras nao.',
    'unidade_de_reamostragem': 'operacao unitaria presente nas duas tabelas',
    'a_linha_do_gerador': 'al = -por_tipo if np.nanmean(por_tipo) < 0 else por_tipo',
    'por_que_a_S30_nao_usa_a_regra_da_S18':
        'uma combinacao de atributos nao tem direcao declarada por fonte nenhuma: a fonte '
        'declara direcao para o atributo, nao para o z-score de varios somados.',
    'n_pares_diretos': len(pares),
    'a_magnitude_e_a_mesma_em_todos': magnitude_bate,
    'invertem_de_sinal': invertem,
    'ficam_iguais': iguais,
    '_leitura_do_padrao': 'invertem exatamente as operacoes cuja direcao declarada contraria '
                          'o que os dados mostram; onde as duas concordam, o valor e o mesmo.',
    'por_operacao': pares,
    '⭐_A_CONSEQUENCIA': {
        'desigualdade': '|rho| >= rho_alinhado, sempre',
        'logo': 'a porta dos compostos e MAIS PERMISSIVA que a das operacoes',
        'e_mesmo_assim': '%d de %d compostos sao elegiveis'
                         % (sum(1 for c in comb['por_combinacao']
                                if c['elegivel_pelas_duas_portas_mensuraveis']),
                            len(comb['por_combinacao'])),
        'portanto': 'a conclusao «nenhum composto elegivel» e CONSERVADORA: sob a orientacao '
                    'estrita da fonte, nenhum passaria tambem.',
    },
}
out['leitura'] = (
    'Das %d operacoes que aparecem nas duas tabelas, %d invertem de sinal e %d ficam iguais, '
    'e a MAGNITUDE e a mesma em todas: %s. O que muda e a orientacao, e a da S30 e a mais '
    'permissiva das duas. ⛔ A legenda anterior dizia «reportada sem alinhamento», o que '
    'nao produz esse padrao e foi retratado.'
    % (len(pares), len(invertem), len(iguais),
       'confirmado' if magnitude_bate else '⛔ NAO confirmado'))
json.dump(out, open(QB / 'as_duas_orientacoes_da_triagem.json', 'w'), indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
