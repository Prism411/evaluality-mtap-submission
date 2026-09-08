#!/usr/bin/env python3
"""⭐⭐ «INVERTE EM PELO MENOS UM TIPO» E ACHADO OU E O QUE UMA MOEDA FARIA?

POR QUE EXISTE (08/09/2026). A manchete do artigo diz que TODAS as operacoes com direcao
declarada ordenam a copia degradada acima da original em pelo menos um dos oito tipos.
⚠️ Sozinha, essa frase e fraca: uma moeda honesta em 8 tipos fica abaixo de 50 % em cerca
de metade deles, entao «pelo menos um» e quase certo por acaso. O que separa nao e a
EXISTENCIA da inversao, e a MAGNITUDE dela.

Aqui se conta quantas operacoes tem pelo menos um tipo **significativamente** abaixo do
acaso: binomial exato unilateral em 100 pares por tipo, com Holm sobre TODOS os testes
(15 operacoes x 8 tipos = 120), que e a correcao conservadora.

⚠️ ANCORA: antes de estender, o script REPRODUZ as acuracias por tipo que o artigo publica.
Se a reproducao falhar, ele para — extender numero que nao reproduz e inventar.

PREVISOES, antes de rodar:
  1. as acuracias por tipo reproduzem as publicadas
  2. a maioria das 15 tem pelo menos um tipo significativamente abaixo do acaso
  3. o controle de moeda (sorteio com p=0,5) NAO acumula significancia sob Holm
"""
import json
import random
import sys
from math import comb
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
sys.path.insert(0, str(QB))
import ops_da_literatura as OPS                                     # noqa: E402

SAIDA = QB / 'quantas_invertem_ALEM_DO_ACASO.json'
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']
NIVEIS = [1, 2, 3, 4, 5]


def binom_cauda_baixa(k, n, p=0.5):
    """P(X <= k) sob binomial(n, p): a cauda que interessa e a de INVERSAO."""
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def holm(pvals):
    """Holm-Bonferroni: devolve o dict de p ajustado."""
    itens = sorted(pvals.items(), key=lambda x: x[1])
    m, ajust, corrente = len(itens), {}, 0.0
    for i, (k, p) in enumerate(itens):
        corrente = max(corrente, min(1.0, (m - i) * p))
        ajust[k] = corrente
    return ajust


def main():
    d = json.loads((QB / 'ops_da_literatura_designA.json').read_text())['por_segmento']
    segs = sorted(d)
    # ⛔ o conjunto e o do ARTIGO, nao «tudo que tem direcao»: o designA carrega tambem
    # operacoes fora do inventario auditado (`sobel_cv`, `qaroush_ct`, `qaroush_ses`,
    # `qaroush_movimento`), e `sobel_cv` nem tem `orig` neste arquivo.
    do_artigo = sorted(json.loads((QB / 'as_15_na_regra_do_artigo.json').read_text())['por_operacao'])
    com_direcao = [o for o in do_artigo if OPS.DIRECAO.get(o) is not None
                   and any(d[s].get(o, {}).get('orig') is not None for s in segs)]
    assert len(com_direcao) == 15, ('⛔ mudou o conjunto das quinze', len(com_direcao), com_direcao)

    acc, cont, emp = {}, {}, {}
    for o in com_direcao:
        maior_e_melhor = OPS.DIRECAO[o]
        acc[o], cont[o], emp[o] = {}, {}, {}
        for t in TIPOS:
            certos = n = empates = 0
            for s in segs:
                v = d[s].get(o)
                if not v or 'orig' not in v:
                    continue
                for lv in NIVEIS:
                    deg = v.get('%s_%d' % (t, lv))
                    if deg is None:
                        continue
                    # ⛔ a tabela publicada tira o EMPATE do denominador, e por isso a
                    # minha primeira conta divergia em 14 celulas: `ke_hue_count` empata
                    # em 22 dos 100 pares de `rescale`, e 11/78 e o 14,1 % publicado.
                    if v['orig'] == deg:
                        empates += 1
                        continue
                    n += 1
                    certos += int(v['orig'] > deg if maior_e_melhor else v['orig'] < deg)
            acc[o][t] = round(100 * certos / n, 1) if n else None
            cont[o][t] = (certos, n)
            emp[o][t] = empates

    # ⛔ ANCORA: as acuracias tem de bater com as publicadas na TABELA_FINAL
    tab = {l['nome']: l['acc'] for l in json.loads((QB / 'TABELA_FINAL.json').read_text())['linhas']}
    conferidas = divergentes = 0
    for o in com_direcao:
        if o not in tab:
            continue
        for t in TIPOS:
            if acc[o][t] is None or t not in tab[o]:
                continue
            conferidas += 1
            if abs(acc[o][t] - tab[o][t]) > 0.05:
                divergentes += 1
    assert conferidas >= 80 and divergentes == 0, \
        '⛔ a reproducao das acuracias publicadas falhou: %d de %d divergem' % (divergentes, conferidas)

    # o teste: por tipo, binomial unilateral, e Holm sobre os 15 x 8
    brutos = {'%s|%s' % (o, t): binom_cauda_baixa(*cont[o][t])
              for o in com_direcao for t in TIPOS if cont[o][t][1]}
    aj = holm(brutos)
    por_op = {}
    for o in com_direcao:
        sig = [t for t in TIPOS if aj.get('%s|%s' % (o, t), 1) < .05]
        abaixo = [t for t in TIPOS if acc[o][t] is not None and acc[o][t] < 50]
        por_op[o] = {'acuracia_por_tipo': acc[o], 'tipos_abaixo_de_50': abaixo,
                     'tipos_significativos': sig, 'n_significativos': len(sig),
                     'menor_acuracia': min(v for v in acc[o].values() if v is not None)}

    # ⚠️ controle: uma moeda honesta, mesmo desenho, tem de NAO acumular significancia
    r = random.Random(42)
    moeda = {}
    for i in range(len(com_direcao)):
        for t in TIPOS:
            k = sum(1 for _ in range(100) if r.random() < .5)
            moeda['moeda%d|%s' % (i, t)] = binom_cauda_baixa(k, 100)
    aj_moeda = holm(moeda)
    moedas_com_sig = len({k.split('|')[0] for k, v in aj_moeda.items() if v < .05})

    n_com_sig = sum(1 for v in por_op.values() if v['n_significativos'])
    n_com_abaixo = sum(1 for v in por_op.values() if v['tipos_abaixo_de_50'])
    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_por_que_existe': ('«inverte em pelo menos um tipo» e quase certo por acaso; o que '
                            'separa e quantas invertem ALEM do acaso'),
        '_ancora': 'as %d celulas conferidas reproduzem a tabela publicada' % conferidas,
        'n_operacoes_com_direcao': len(com_direcao),
        'n_pares_por_tipo': '100 menos os empates, como a tabela publicada conta',
        'empates_por_operacao': {o: sum(emp[o].values()) for o in com_direcao}, 'n_testes': len(brutos), 'correcao': 'Holm sobre os 120',
        'com_ao_menos_um_tipo_abaixo_de_50': n_com_abaixo,
        'com_ao_menos_um_tipo_SIGNIFICATIVO': n_com_sig,
        'controle_da_moeda': {'operacoes_simuladas': len(com_direcao),
                              'quantas_acumulam_significancia': moedas_com_sig},
        'por_operacao': por_op,
    }
    res['previsoes'] = {
        '1_as_acuracias_reproduzem': 'CONFIRMADA',
        '2_a_maioria_tem_tipo_significativo':
            'CONFIRMADA' if n_com_sig > len(com_direcao) / 2 else '⛔ FALHOU',
        '3_a_moeda_nao_acumula': 'CONFIRMADA' if moedas_com_sig == 0 else '⛔ FALHOU',
    }
    res['leitura'] = (
        '%d das %d operacoes com direcao declarada tem pelo menos um tipo abaixo de 50 %%, e '
        '%d delas tem pelo menos um tipo abaixo do acaso com significancia sob Holm nos 120 '
        'testes. A moeda de controle, no mesmo desenho, acumula significancia em %d.'
        % (n_com_abaixo, len(com_direcao), n_com_sig, moedas_com_sig))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for k, v in res['previsoes'].items():
        print(' ', k, '=', v)
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
