#!/usr/bin/env python3
"""⭐ OS DOIS EIXOS DO ARTIGO SE PREVEEM? (E A RESPOSTA NAO ENTRA NO CORPO)

POR QUE EXISTE (08/09/2026). O artigo mede cada operacao em dois eixos independentes: a
resposta a degradacao controlada no KADID e a concordancia com o modelo de referencia nos 42
clusters. Se um previsse o outro, a triagem seria redundante com o piso; se nao, os dois
medem coisas diferentes e a conjuncao faz sentido.

⛔ NAO ENTRA NO CORPO. Com n = 9 operacoes, o Spearman da -0,31 com p 0,41: e um NULO SEM
PODER, e reportar «os eixos sao independentes» seria trocar ausencia de evidencia por
evidencia de ausencia, que e o que o artigo evita em toda parte.

⭐ O QUE SOBREVIVE E UM PAR CONCRETO, que nao precisa de teste: a operacao com a MAIOR
sensibilidade a dano (`ke_edge_distribution`, +0,298) tem a MENOR concordancia in-domain de
todas (kappa -0,258). Isso e uma leitura direta de dois numeros ja publicados, nao uma
correlacao — e serve para quem quiser argumentar que um eixo substitui o outro.
"""
import json
import random
from pathlib import Path

QB = Path('/data/projects/benchmark')


def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)


SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / 'os_dois_eixos_se_preveem.json'


def postos(v):
    s = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
            j += 1
        m = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[s[k]] = m
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = postos(a), postos(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** .5
    return num / den if den else float('nan')


def main():
    q = json.loads(_raiz('as_15_na_regra_do_artigo.json').read_text(encoding='utf-8'))['por_operacao']
    piso = {x['operacao']: x for x in
            json.loads(_raiz('o_piso_das_operacoes_isoladas_e_estavel.json')
                       .read_text(encoding='utf-8'))['por_operacao']}
    ops = [o for o in q if o in piso and o != 'si']
    xs = [q[o]['sensibilidade_media'] for o in ops]
    ys = [piso[o]['kappa'] for o in ops]
    rho = spearman(xs, ys)
    r = random.Random(42)
    B, piores = 20000, 0
    for _ in range(B):
        yy = ys[:]
        r.shuffle(yy)
        piores += abs(spearman(xs, yy)) >= abs(rho)
    p = (piores + 1) / (B + 1)
    melhor_sens = max(ops, key=lambda o: q[o]['sensibilidade_media'])
    pior_piso = min(ops, key=lambda o: piso[o]['kappa'])
    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        'n_operacoes': len(ops),
        'spearman': round(rho, 4), 'p_permutacional': round(p, 4), 'B': B,
        'por_operacao': {o: {'sensibilidade': q[o]['sensibilidade_media'],
                             'piso_kappa': round(piso[o]['kappa'], 4)} for o in ops},
        '⭐_o_par_que_dispensa_teste': {
            'maior_sensibilidade': melhor_sens,
            'sensibilidade': q[melhor_sens]['sensibilidade_media'],
            'piso_kappa_dessa_mesma': round(piso[melhor_sens]['kappa'], 4),
            'e_a_menor_de_todas': melhor_sens == pior_piso},
        '⛔_NAO_ENTRA_NO_CORPO': (
            'n = %d e p = %.2f: nulo SEM PODER. Reportar «os eixos sao independentes» seria '
            'trocar ausencia de evidencia por evidencia de ausencia. Fica arquivado para '
            'impedir que alguem AFIRME a associacao sem medir.' % (len(ops), p)),
    }
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print('  Spearman %+.4f, p %.4f, n %d' % (rho, p, len(ops)))
    print('  par que dispensa teste:', res['⭐_o_par_que_dispensa_teste'])


if __name__ == '__main__':
    main()
