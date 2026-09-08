#!/usr/bin/env python3
"""⭐⭐ A SUBSTITUICAO PELO LIQE CONCORDA COM A OPERACAO IMPLANTADA ACIMA DO ACASO?

POR QUE EXISTE (08/09/2026). O corpo diz «trocar a operacao implantada pela do LIQE muda 22
dos 42 representantes». Sobra a pergunta que um revisor faz em seguida: **os 20 que NAO
mudam sao concordancia, ou sao o que o acaso entrega?** Com 36 dos 42 clusters binarios, o
acaso ja acerta 47,0 % sozinho, entao «20 de 42» pode ser exatamente nada.

⚠️ O TESTE SO SEPARA COM O CONTROLE. Um teste que aprova tudo nao responde: por isso entram
duas linhas de calibracao com resposta conhecida — duas implementacoes IDENTICAS (que tem
de ficar ACIMA do acaso) e um sorteio (que tem de ficar indistinguivel dele).

⚠️ A unidade e o BLOCO DE TOPICO, que e a unidade declarada para as analises dos 42
clusters (Tabela S27 do suplementar). O binomial exato entra como analise de sensibilidade.

PREVISOES, antes de rodar:
  1. o acaso medio dos 42 clusters reproduz o 0,4702 publicado
  2. a concordancia LIQE x implantada NAO se distingue do acaso (IC cruza o acaso)
  3. o controle de implementacoes identicas SE distingue (IC acima do acaso)
  4. o controle de sorteio NAO se distingue
"""
import json
import random
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
CTRL = QB / 'same_frame_same_pooling_control.json'
TERC = Path('/home/jader/memoria-agentes/07-Artigos/evaluality-literatura/'
            'third_revision_reanalysis.json')
SAIDA = QB / 'a_substituicao_concorda_acima_do_acaso.json'
B, SEMENTE = 10000, 42


def topico(cid):
    return cid.split('#')[0]


def ic_bloco_de_topico(por_cluster, b=B, semente=SEMENTE):
    """Reamostra TOPICOS, nao clusters: os 42 vem de 19 topicos e nao sao independentes."""
    porto = {}
    for cid, v in por_cluster.items():
        porto.setdefault(topico(cid), []).append(v)
    chaves = sorted(porto)
    r = random.Random(semente)
    dist = []
    for _ in range(b):
        am = []
        for _ in range(len(chaves)):
            am += porto[chaves[r.randrange(len(chaves))]]
        dist.append(sum(am) / len(am))
    dist.sort()
    return dist[int(.025 * b)], dist[int(.975 * b)]


def main():
    c = json.loads(CTRL.read_text())['clusters']
    t = json.loads(TERC.read_text())['same_frame_same_pooling']
    assert len(c) == 42 and t['n_clusters'] == 42

    tam = {k: len(v['segments']) for k, v in c.items()}
    acaso = sum(1 / n for n in tam.values()) / len(tam)

    # ⚠️ o conjunto que o CORPO cita e o da operacao completa, nao o do braco casado:
    # os dois valem 22 e sao conjuntos diferentes (ver a memoria dos dois «22 de 42»).
    muda = set(t['published_change_clusters'])
    concorda = {k: (0 if k in muda else 1) for k in c}

    # controle A: duas implementacoes identicas concordam sempre, e tem de separar
    ident = {k: 1 for k in c}
    # controle B: um sorteio dentro de cada cluster, que NAO pode separar
    r = random.Random(SEMENTE)
    sorteio = {k: (1 if r.randrange(tam[k]) == r.randrange(tam[k]) else 0) for k in c}

    out = {}
    for nome, d in (('liqe_x_implantada', concorda), ('controle_identicas', ident),
                    ('controle_sorteio', sorteio)):
        p = sum(d.values()) / len(d)
        lo, hi = ic_bloco_de_topico(d)
        out[nome] = {'acertos': sum(d.values()), 'de': len(d), 'pct': round(100 * p, 1),
                     'ic_bloco_de_topico': [round(100 * lo, 1), round(100 * hi, 1)],
                     'separa_do_acaso': lo > acaso,
                     'kappa_contra_o_acaso': round((p - acaso) / (1 - acaso), 4)}

    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_por_que_existe': ('o corpo diz que a substituicao muda 22 de 42; faltava dizer se '
                            'os 20 que ficam sao concordancia ou sao o acaso'),
        '_unidade': 'bloco de topico (19 topicos, 42 clusters), a unidade declarada',
        'n_clusters': len(c), 'n_topicos': len({topico(k) for k in c}),
        'tamanhos': {str(n): sum(1 for v in tam.values() if v == n) for n in sorted(set(tam.values()))},
        'acaso_medio': round(acaso, 4),
        'B': B, 'semente': SEMENTE,
        'por_linha': out,
    }
    res['previsoes'] = {
        '1_o_acaso_reproduz_o_publicado': 'CONFIRMADA' if abs(acaso - .4702) < 5e-4 else '⛔ FALHOU',
        '2_a_substituicao_NAO_separa_do_acaso':
            'CONFIRMADA' if not out['liqe_x_implantada']['separa_do_acaso'] else '⛔ FALHOU',
        '3_o_controle_de_identicas_SEPARA':
            'CONFIRMADA' if out['controle_identicas']['separa_do_acaso'] else '⛔ FALHOU',
        '4_o_controle_de_sorteio_NAO_separa':
            'CONFIRMADA' if not out['controle_sorteio']['separa_do_acaso'] else '⛔ FALHOU',
    }
    res['leitura'] = (
        'a concordancia que sobra depois da substituicao e de %.1f %% contra um acaso de '
        '%.1f %%, kappa %.4f, e o intervalo por bloco de topico cruza o acaso: os 20 '
        'clusters que NAO mudam nao sao evidencia de acordo entre a operacao implantada e '
        'um modelo validado.' % (out['liqe_x_implantada']['pct'], 100 * acaso,
                                 out['liqe_x_implantada']['kappa_contra_o_acaso']))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for k, v in res['previsoes'].items():
        print(' ', k, '=', v)
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
