#!/usr/bin/env python3
"""⛔ O TESTE DAS 120 CELULAS RESPEITA A UNIDADE DE DEPENDENCIA DO PROPRIO DESENHO?

POR QUE EXISTE (09/09/2026). O corpo passou a dizer que cada celula operacao-tipo recebe um
binomial exato unilateral contra o nulo de 0,50. ⛔ Mas os 100 pares de uma celula sao 20
SEGMENTOS x 5 NIVEIS, e os cinco niveis de um segmento compartilham o conteudo: o proprio
metodo declara o segmento como unidade e usa block-bootstrap por segmento nos intervalos.
Tratar os 100 como Bernoulli independentes e ANTICONSERVADOR.

⭐ O TESTE CERTO, na unidade declarada: troca de sinal POR SEGMENTO. Sob o nulo de ausencia
de preferencia direcional, inverter TODOS os cinco resultados de um segmento e equiprovavel,
o que preserva a dependencia interna. Com 20 segmentos a nula tem 2^20 pontos, e a
distribuicao sai EXATA por convolucao — nao ha amostragem aqui.

⚠️ Este script NAO re-roda benchmark nenhum: le as mesmas decisoes ja salvas e refaz so a
inferencia.

PREVISOES, antes de rodar:
  1. o p em bloco e >= o p binomial em toda celula (o binomial e anticonservador)
  2. as celulas com acuracia 0 de 100 continuam significativas, porque nenhuma troca de
     sinal as explica
  3. alguma celula de margem PERDE a significancia: se nenhuma perder, o teste antigo nao
     estava inflando nada e a troca seria so cosmetica
"""
import json
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

QB = Path('/data/projects/benchmark')


def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(QB))
import ops_da_literatura as OPS                                     # noqa: E402

SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / 'o_binomial_respeita_o_bloco.json'
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']
NIVEIS = [1, 2, 3, 4, 5]


def p_binomial(k, n):
    """O teste ANTIGO: os n pares como n Bernoulli independentes."""
    return float(sum(comb(n, i) for i in range(k + 1))) / float(2 ** n) if n else 1.0


def p_bloco(por_segmento):
    """Troca de sinal por SEGMENTO, nula exata por convolucao.

    `por_segmento` e [(certos, n)] de cada segmento. Sob o nulo, cada segmento contribui
    `certos` ou `n - certos`, com probabilidade 1/2 cada. A soma observada e o total de
    acertos, e o p unilateral e P(total_nulo <= total_observado).
    """
    dist = {0: Fraction(1)}
    for c, n in por_segmento:
        novo = {}
        for t, w in dist.items():
            for add in (c, n - c):
                novo[t + add] = novo.get(t + add, Fraction(0)) + w / 2
        dist = novo
    obs = sum(c for c, _ in por_segmento)
    return float(sum(w for t, w in dist.items() if t <= obs))


def holm(p):
    itens = sorted(p.items(), key=lambda x: x[1])
    m, aj, corr = len(itens), {}, 0.0
    for i, (k, v) in enumerate(itens):
        corr = max(corr, min(1.0, (m - i) * v))
        aj[k] = corr
    return aj


def main():
    d = json.loads(_raiz('ops_da_literatura_designA.json').read_text())['por_segmento']
    segs = sorted(d)
    do_artigo = sorted(json.loads(_raiz('as_15_na_regra_do_artigo.json').read_text())['por_operacao'])
    ops = [o for o in do_artigo if OPS.DIRECAO.get(o) is not None
           and any(d[s].get(o, {}).get('orig') is not None for s in segs)]
    assert len(ops) == 15, ('⛔ mudou o conjunto das quinze', len(ops))

    celulas = {}
    for o in ops:
        maior = OPS.DIRECAO[o]
        for t in TIPOS:
            por_seg, tot_c, tot_n = [], 0, 0
            for s in segs:
                v = d[s].get(o)
                if not v or 'orig' not in v:
                    continue
                c = n = 0
                for lv in NIVEIS:
                    deg = v.get('%s_%d' % (t, lv))
                    if deg is None or v['orig'] == deg:   # empate fora, como a tabela conta
                        continue
                    n += 1
                    c += int(v['orig'] > deg if maior else v['orig'] < deg)
                if n:
                    por_seg.append((c, n))
                    tot_c += c
                    tot_n += n
            if tot_n:
                celulas['%s|%s' % (o, t)] = {
                    'acuracia': round(100 * tot_c / tot_n, 1), 'certos': tot_c, 'de': tot_n,
                    'n_segmentos': len(por_seg),
                    'p_binomial': p_binomial(tot_c, tot_n),
                    'p_bloco_de_segmento': p_bloco(por_seg)}

    aj_bin = holm({k: v['p_binomial'] for k, v in celulas.items()})
    aj_blo = holm({k: v['p_bloco_de_segmento'] for k, v in celulas.items()})
    abaixo = [k for k, v in celulas.items() if v['acuracia'] < 50]
    sig_bin = [k for k in abaixo if aj_bin[k] < .05]
    sig_blo = [k for k in abaixo if aj_blo[k] < .05]
    perdem = [k for k in sig_bin if k not in sig_blo]
    ops_blo = len({k.split('|')[0] for k in sig_blo})
    anticons = sum(1 for k, v in celulas.items()
                   if v['p_bloco_de_segmento'] + 1e-12 < v['p_binomial'])

    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_teste': 'troca de sinal por segmento, nula exata por convolucao sobre 2^20 pontos',
        'n_celulas': len(celulas), 'n_operacoes': len(ops),
        'celulas_abaixo_do_acaso': len(abaixo),
        'significativas_sob_o_binomial_antigo': len(sig_bin),
        'significativas_sob_o_bloco_de_segmento': len(sig_blo),
        'perdem_a_significancia_no_bloco': sorted(perdem),
        'operacoes_com_ao_menos_uma_significativa_no_bloco': ops_blo,
        'celulas_em_que_o_bloco_da_p_MENOR_que_o_binomial': anticons,
        'por_celula': {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv)
                           for kk, vv in v.items()} for k, v in sorted(celulas.items())},
    }
    res['previsoes'] = {
        '1_o_bloco_nunca_da_p_menor': 'CONFIRMADA' if anticons == 0 else '⛔ FALHOU em %d' % anticons,
        '2_as_de_zero_continuam': 'CONFIRMADA' if all(
            aj_blo[k] < .05 for k, v in celulas.items() if v['acuracia'] == 0.0) else '⛔ FALHOU',
        '3_alguma_de_margem_perde': 'CONFIRMADA' if perdem else '⚠️ NENHUMA PERDE',
    }
    res['leitura'] = (
        'sob o binomial que trata os pares como independentes, %d das %d celulas abaixo do '
        'acaso sobrevivem a Holm; sob a troca de sinal POR SEGMENTO, que e a unidade que o '
        'metodo declara, sobrevivem %d, em %d das %d operacoes. %s'
        % (len(sig_bin), len(abaixo), len(sig_blo), ops_blo, len(ops),
           ('Perdem a significancia: ' + ', '.join(perdem)) if perdem
           else 'Nenhuma celula muda de veredito.'))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
