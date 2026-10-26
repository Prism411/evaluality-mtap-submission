#!/usr/bin/env python3
"""⛔ A FUSAO DAS FONTES PARTILHADAS, QUE OS PARES FAZEM, MUDA A APLICACAO?

POR QUE EXISTE (22/09/2026, parecer v4, ponto 2.4). Nos pares construidos o artigo funde
`cessar_fogo_ucrania` e `ucrania` num so bloco, porque os dois rotulos partilham os tres
`.mp4` de origem: sao 12 blocos, nao 13. ⛔ **Na aplicacao os dois continuam entrando como
topicos separados**, e o intervalo por bloco de topico reamostra 19 chaves.

⚠️ O revisor nao afirma que o intervalo esta errado. Afirma que a MESMA dependencia,
reconhecida numa analise, nao foi tratada na outra. Isto mede o efeito.

⭐ PREVISOES, declaradas ANTES de rodar:
  1. a fusao existe de fato na aplicacao: os dois rotulos aparecem e partilham fonte;
  2. o veredito NAO muda — o intervalo continua do mesmo lado do acaso;
  3. a largura muda pouco, porque e um bloco a menos em 19.
⚠️ Se a 2 falhar, o corpo precisa do numero fundido, nao de uma nota de rodape.
"""
import json
import random
from pathlib import Path

H = Path(__file__).resolve().parent


def _raiz(nome):
    """Os dois arquivos de reanalise moram na pasta do artigo; no clone, em derived_data."""
    for base in (H, H / 'derived_data',
                 Path('/home/user/workspace/07-Artigos/manuscript'),
                 Path('/data/projects/submission-package/reproducibility/derived_data')):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)
FUNDIR = {'cessar_fogo_ucrania': 'ucrania'}
B, SEMENTE = 10000, 42
SAIDA = H / 'a_fusao_de_fontes_vale_na_aplicacao.json'


def topico(cid, fundir):
    t = cid.split('#')[0]
    return FUNDIR.get(t, t) if fundir else t


def ic(por_cluster, fundir, b=B, semente=SEMENTE):
    porto = {}
    for cid, v in por_cluster.items():
        porto.setdefault(topico(cid, fundir), []).append(v)
    chaves = sorted(porto)
    r = random.Random(semente)
    dist = []
    for _ in range(b):
        am = []
        for _ in range(len(chaves)):
            am += porto[chaves[r.randrange(len(chaves))]]
        dist.append(sum(am) / len(am))
    dist.sort()
    return dist[int(.025 * b)], dist[int(.975 * b)], len(chaves)


def ok(v):
    return 'CONFIRMADA' if v else '⛔ FALHOU'


def main():
    base = json.load(open(H / 'a_substituicao_concorda_acima_do_acaso.json'))
    # ⭐ o vetor por cluster e RECONSTRUIDO das mesmas fontes que a apuracao original usa,
    #    com o mesmo assert de 42, para nao depender de um cache que ela nao grava.
    c = json.loads(_raiz('same_frame_same_pooling_control.json').read_text())['clusters']
    t3 = json.loads(_raiz('third_revision_reanalysis.json').read_text())['same_frame_same_pooling']
    assert len(c) == 42 and t3['n_clusters'] == 42, '⛔ o material mudou: refazer a apuracao'
    tam = {k: len(v['segments']) for k, v in c.items()}
    muda = set(t3['published_change_clusters'])
    r0 = random.Random(SEMENTE)
    bruto = {
        'liqe_x_implantada': {k: (0 if k in muda else 1) for k in c},
        'controle_identicas': {k: 1 for k in c},
        'controle_sorteio': {k: (1 if r0.randrange(tam[k]) == r0.randrange(tam[k]) else 0)
                             for k in c},
    }
    # ⛔ controle do reconstrutor: se o IC sem fundir nao reproduzir o publicado, o vetor
    #    que montei nao e o que a apuracao usou, e nada abaixo vale.
    _lo, _hi, _n = ic(bruto['liqe_x_implantada'], False)
    _pub = base['por_linha']['liqe_x_implantada']['ic_bloco_de_topico']
    assert [round(100 * _lo, 1), round(100 * _hi, 1)] == _pub, (
        '⛔ o reconstrutor NAO reproduz o IC publicado %s != %s' % (
            [round(100 * _lo, 1), round(100 * _hi, 1)], _pub))
    r = {'_o_que_e': __doc__, 'previsoes': {}, 'por_linha': {}}
    for linha, pc in bruto.items():
        lo13, hi13, n13 = ic(pc, False)
        lo12, hi12, n12 = ic(pc, True)
        r['por_linha'][linha] = {
            'sem_fundir': {'n_blocos': n13, 'ic': [round(100 * lo13, 1), round(100 * hi13, 1)]},
            'fundido':    {'n_blocos': n12, 'ic': [round(100 * lo12, 1), round(100 * hi12, 1)]},
            'delta_largura': round(100 * ((hi12 - lo12) - (hi13 - lo13)), 2)}
    acaso = 100 * base['acaso_medio']
    lado = lambda ic_: 'acima' if ic_[0] > acaso else ('abaixo' if ic_[1] < acaso else 'cruza')
    muda = [k for k, v in r['por_linha'].items()
            if lado(v['sem_fundir']['ic']) != lado(v['fundido']['ic'])]
    r['acaso_medio_pct'] = round(acaso, 1)
    r['linhas_que_mudam_de_veredito'] = muda
    r['previsoes']['1_os_dois_rotulos_estao_na_aplicacao'] = ok(
        any(t in {c.split('#')[0] for pc in bruto.values() for c in pc}
            for t in ('cessar_fogo_ucrania', 'ucrania')))
    r['previsoes']['2_o_veredito_nao_muda'] = ok(not muda)
    r['previsoes']['3_a_largura_muda_pouco'] = ok(
        all(abs(v['delta_largura']) < 5 for v in r['por_linha'].values()))
    SAIDA.write_text(json.dumps(r, indent=1, ensure_ascii=False))
    for k, v in r['previsoes'].items():
        print(f"  {'✅' if v == 'CONFIRMADA' else '⛔'} {k}: {v}")
    for k, v in r['por_linha'].items():
        print(f"  {k:24s} 19 blocos {v['sem_fundir']['ic']}  ->  "
              f"{v['fundido']['n_blocos']} blocos {v['fundido']['ic']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
