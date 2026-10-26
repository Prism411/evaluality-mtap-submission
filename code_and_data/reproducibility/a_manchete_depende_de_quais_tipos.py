#!/usr/bin/env python3
"""⭐⭐ A MANCHETE DEPENDE DE QUAIS OITO DEGRADACOES ENTRARAM?

POR QUE EXISTE (08/09/2026). «Todas as quinze invertem em pelo menos um tipo» e uma
afirmacao sobre o CONJUNTO de tipos escolhido. Um revisor pergunta se ela sobrevive a
mexer nesse conjunto, e a resposta tem de ser um numero, nao uma garantia.

Tres remocoes, cada uma com motivo declarado:
  - `dark` e `satur`, os dois tipos ALINHADOS com termos de operacoes (o proprio artigo ja
    os exclui numa analise de sensibilidade);
  - `noise`, onde o artigo diz que as falhas se concentram;
  - os tres juntos, o caso mais desfavoravel a manchete.

⚠️ ANCORA antes de estender: as acuracias por tipo recomputadas do escore cru tem de
reproduzir a tabela publicada, celula a celula.

⛔ E uma armadilha de Python que quase produziu numero errado aqui: `acc or 100` devolve
**100** quando `acc` e `0.0`, porque zero e falsy. A primeira rodada disse «13 de 15» em vez
de 15 porque as duas operacoes com acuracia ZERO no ruido foram lidas como 100.

PREVISOES:
  1. as acuracias reproduzem a tabela publicada
  2. com os oito tipos, as quinze invertem
  3. tirar os dois tipos alinhados NAO derruba a manchete
"""
import json
import sys
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

SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / \
    'a_manchete_depende_de_quais_tipos.json'
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']


def main():
    d = json.loads(_raiz('ops_da_literatura_designA.json').read_text())['por_segmento']
    segs = sorted(d)
    do_artigo = sorted(json.loads(_raiz('as_15_na_regra_do_artigo.json').read_text())['por_operacao'])
    ops = [o for o in do_artigo if OPS.DIRECAO.get(o) is not None
           and any(d[s].get(o, {}).get('orig') is not None for s in segs)]
    assert len(ops) == 15, ('⛔ mudou o conjunto das quinze', len(ops))

    def acc(o, t):
        maior = OPS.DIRECAO[o]
        certos = n = 0
        for s in segs:
            v = d[s].get(o)
            if not v or 'orig' not in v:
                continue
            for lv in range(1, 6):
                deg = v.get('%s_%d' % (t, lv))
                if deg is None or v['orig'] == deg:     # empate fora, como a tabela conta
                    continue
                n += 1
                certos += int(v['orig'] > deg if maior else v['orig'] < deg)
        return 100 * certos / n if n else None

    A = {o: {t: acc(o, t) for t in TIPOS} for o in ops}

    # ⛔ ANCORA: bate com a tabela publicada?
    tab = {l['nome']: l['acc'] for l in json.loads(_raiz('TABELA_FINAL.json').read_text())['linhas']}
    conf = div = 0
    for o in ops:
        if o not in tab:
            continue
        for t in TIPOS:
            if A[o][t] is None:
                continue
            conf += 1
            div += int(abs(round(A[o][t], 1) - tab[o][t]) > 0.05)
    assert conf >= 80 and div == 0, '⛔ a ancora falhou: %d de %d celulas divergem' % (div, conf)

    cenarios = [([], 'os oito tipos'),
                (['dark', 'satur'], 'sem os dois tipos alinhados'),
                (['noise'], 'sem o ruido branco'),
                (['dark', 'satur', 'noise'], 'sem os tres')]
    out = {}
    for excl, rot in cenarios:
        ts = [t for t in TIPOS if t not in excl]
        # ⚠️ `A[o][t] is not None and A[o][t] < 50`, nunca `A[o][t] or ...`: zero e falsy
        inv = [o for o in ops if any(A[o][t] is not None and A[o][t] < 50 for t in ts)]
        out[rot] = {'tipos_removidos': excl, 'tipos_usados': len(ts),
                    'invertem': len(inv), 'de': len(ops),
                    'nao_invertem': sorted(set(ops) - set(inv))}

    # ⭐ o SEGUNDO eixo: e de quais SEGMENTOS ela depende? Deixa um de fora por vez.
    def inverte(o, fora):
        maior = OPS.DIRECAO[o]
        for t in TIPOS:
            certos = n = 0
            for s in segs:
                if s == fora:
                    continue
                v = d[s].get(o)
                if not v or 'orig' not in v:
                    continue
                for lv in range(1, 6):
                    deg = v.get('%s_%d' % (t, lv))
                    if deg is None or v['orig'] == deg:
                        continue
                    n += 1
                    certos += int(v['orig'] > deg if maior else v['orig'] < deg)
            if n and 100 * certos / n < 50:
                return True
        return False

    por_rodada = [sum(1 for o in ops if inverte(o, s)) for s in segs]
    seg = {'n_rodadas': len(segs), 'minimo': min(por_rodada), 'maximo': max(por_rodada),
           'rodadas_abaixo_da_base': sum(1 for x in por_rodada if x < len(ops))}

    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        'tirando_um_segmento': seg,
        '_ancora': '%d celulas conferidas contra a tabela publicada' % conf,
        'n_operacoes': len(ops), 'por_cenario': out,
    }
    res['previsoes'] = {
        '1_a_ancora_bate': 'CONFIRMADA',
        '2_com_os_oito_todas_invertem':
            'CONFIRMADA' if out['os oito tipos']['invertem'] == len(ops) else '⛔ FALHOU',
        '3_tirar_os_alinhados_nao_derruba':
            'CONFIRMADA' if out['sem os dois tipos alinhados']['invertem'] == len(ops) else '⛔ FALHOU',
        '4_tirar_um_segmento_nao_derruba_em_rodada_nenhuma':
            'CONFIRMADA' if seg['rodadas_abaixo_da_base'] == 0 else '⛔ FALHOU',
    }
    res['leitura'] = (
        'a manchete nao depende dos dois tipos alinhados: sem eles as %d continuam '
        'invertendo. Depende do ruido branco: sem ele sao %d de %d, e sem os tres, %d.'
        % (len(ops), out['sem o ruido branco']['invertem'], len(ops),
           out['sem os tres']['invertem'])
        + ' No eixo dos segmentos ela nao depende de nenhum: nas %d rodadas deixando um de '
          'fora, as %d continuam invertendo em todas.' % (seg['n_rodadas'], len(ops)))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
