#!/usr/bin/env python3
"""⭐ QUANTAS ESCOLHAS DISTINTAS AS QUATORZE OPERACOES PRODUZEM EM CADA CLUSTER?

POR QUE EXISTE (08/09/2026). O corpo diz que «o cluster medio extrai 2,21 escolhas distintas
das quatorze», e esse decimal estava DIGITADO na prosa: o teste de mutacao mostrou que
trocar um decimal digitado passa por todas as 23 guardas. Este arquivo o ancora.

⚠️ A media e sobre os 42 clusters, e o teto de cada um e o TAMANHO dele: um cluster binario
nao pode dar mais de duas escolhas distintas. Por isso a media vem junto do teto medio, que
e o que a torna legivel.

⭐ E O QUE A ANCORA ACHOU: a media de escolhas distintas e IDENTICA ao tamanho medio do
cluster, e a distribuicao das duas coincide. Em todos os 42 clusters as quatorze operacoes
escolhem TODOS os membros — inclusive nos seis com tres ou quatro segmentos. Ou seja, o 2,21
nao e um valor modesto: e o TETO que os tamanhos permitem, saturado.

PREVISOES:
  1. sao 42 clusters e 14 operacoes
  2. a media de escolhas distintas reproduz o 2,21 publicado
  3. nenhum cluster excede o proprio tamanho
  4. (achada ao rodar) todos os 42 saturam: distintas == tamanho
"""
import json
from pathlib import Path

QB = Path('/data/projects/benchmark')

# ⚠️ mesma resolucao dos outros: rodando do pacote, os insumos estao em `derived_data/`.
def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)

SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / 'quantas_escolhas_distintas_por_cluster.json'
PUBLICADO = 2.21


def main():
    d = json.loads(_raiz('efeito_a_jusante.json').read_text(encoding='utf-8'))['topicos']
    clusters = [c for t in d.values() for c in t['clusters']]
    ops = sorted({o for c in clusters for o in c['escores']})
    distintas, tamanhos = [], []
    for c in clusters:
        vencedores = set()
        for o in ops:
            e = c['escores'].get(o)
            if not e:
                continue
            vencedores.add(max(e, key=e.get))
        distintas.append(len(vencedores))
        tamanhos.append(c['n'])
    media = sum(distintas) / len(distintas)
    excede = sum(1 for v, n in zip(distintas, tamanhos) if v > n)
    saturam = sum(1 for v, n in zip(distintas, tamanhos) if v == n)
    grandes = sum(1 for n in tamanhos if n > 2)
    grandes_saturam = sum(1 for v, n in zip(distintas, tamanhos) if n > 2 and v == n)
    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_fonte': 'efeito_a_jusante.json',
        'n_clusters': len(clusters), 'n_operacoes': len(ops),
        'media_de_escolhas_distintas': round(media, 4),
        'como_impressa': round(media, 2),
        'publicado': PUBLICADO,
        'reproduz_o_publicado': abs(round(media, 2) - PUBLICADO) < 5e-3,
        'teto_medio_o_tamanho_do_cluster': round(sum(tamanhos) / len(tamanhos), 4),
        'distribuicao': {str(k): distintas.count(k) for k in sorted(set(distintas))},
        'clusters_que_excedem_o_proprio_tamanho': excede,
        'clusters_que_SATURAM_o_proprio_tamanho': saturam,
        'clusters_com_mais_de_dois_membros': grandes,
        'desses_quantos_saturam': grandes_saturam,
    }
    res['previsoes'] = {
        '1_42_clusters_e_14_operacoes':
            'CONFIRMADA' if len(clusters) == 42 and len(ops) == 14 else '⛔ FALHOU',
        '2_reproduz_o_publicado': 'CONFIRMADA' if res['reproduz_o_publicado'] else '⛔ FALHOU',
        '3_nenhum_excede_o_tamanho': 'CONFIRMADA' if excede == 0 else '⛔ FALHOU',
        '4_todos_saturam': 'CONFIRMADA' if saturam == len(clusters) else '⛔ FALHOU',
    }
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    res['leitura'] = (
        'em %d dos %d clusters as %d operacoes escolhem TODOS os membros, e nos %d clusters '
        'com mais de dois segmentos isso vale nos %d: a media de %.2f escolhas distintas e '
        'o teto que os tamanhos permitem, nao um valor intermediario.'
        % (saturam, len(clusters), len(ops), grandes, grandes_saturam, media))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
