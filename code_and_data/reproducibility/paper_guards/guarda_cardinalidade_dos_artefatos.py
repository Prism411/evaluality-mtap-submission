#!/usr/bin/env python3
"""⛔ OS ARTEFATOS PUBLICADOS AINDA TEM O TAMANHO QUE O ARTIGO SUPOE?

POR QUE EXISTE (13/09/2026, apos parecer de revisor). O README declarava que rodar o
diretorio inteiro de uma vez deixou «a two-cluster control file overwrite the shipped
forty-two-cluster one». ⚠️ O `exige.py` impede que isso ACONTECA daqui em diante; esta
guarda detecta se ja aconteceu, porque um arquivo encolhido em silencio nao deixa rastro
alem do proprio tamanho.

⭐ Cada linha e uma CONTAGEM QUE O ARTIGO CITA, e nao um tamanho de arquivo arbitrario: 42
clusters, 800 pares (20 segmentos x 40 condicoes), 20 segmentos amostrados. Se um numero
destes cair, uma tabela do artigo deixou de ter fonte.

Autoteste de duas pernas: o estado atual passa, e um arquivo encolhido REPROVA.
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent

# arquivo -> (caminho de chaves ate o agregado, quantos o artigo supoe, o que o numero e)
ESPERADO = [
    ('derived_data/same_frame_same_pooling_control.json', ['clusters'], 42,
     'os clusters de redundancia do desenho de substituicao'),
    ('derived_data/synth_sift.json', ['data'], 20,
     'os segmentos amostrados para os pares construidos'),
    ('derived_data/synth_scores.json', ['brisque'], 820,
     'as condicoes pontuadas por modelo: 20 segmentos x 41 condicoes'),
]


def desce(o, caminho):
    for k in caminho:
        if not isinstance(o, dict) or k not in o:
            return None
        o = o[k]
    return o


def confere(raiz=None):
    raiz = Path(raiz) if raiz else RAIZ
    faltas, vistos = [], 0
    for rel, caminho, n, oque in ESPERADO:
        p = raiz / rel
        if not p.exists():
            faltas.append('%s: ausente' % rel)
            continue
        try:
            alvo = desce(json.loads(p.read_text(encoding='utf-8')), caminho)
        except Exception as e:
            faltas.append('%s: nao abre (%s)' % (rel, e))
            continue
        if alvo is None:
            faltas.append('%s: nao achei %s' % (rel, '/'.join(caminho)))
            continue
        vistos += 1
        # ⛔ zero esperado e bug: um agregado vazio nunca passa por aqui
        if not len(alvo):
            faltas.append('%s: %s esta VAZIO' % (rel, '/'.join(caminho)))
        elif len(alvo) != n:
            faltas.append('%s: %s tem %d e o artigo supoe %d (%s)'
                          % (rel, '/'.join(caminho), len(alvo), n, oque))
    assert vistos or faltas, '⛔ nada foi conferido: a guarda aprovaria no vacuo'
    return not faltas, faltas, vistos


def _autoteste():
    import tempfile
    ok, f, _ = confere()
    assert ok, '⛔ o estado atual deveria passar: %s' % f
    with tempfile.TemporaryDirectory() as td:
        # ⭐ o mundo errado e o defeito REAL: o controle de 42 clusters com 2
        rel, caminho, _n, _o = ESPERADO[0]
        q = Path(td) / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        orig = json.loads((RAIZ / rel).read_text(encoding='utf-8'))
        cls = orig[caminho[0]]
        orig[caminho[0]] = {k: cls[k] for k in list(cls)[:2]}
        q.write_text(json.dumps(orig))
        for outro, c2, _n2, _o2 in ESPERADO[1:]:
            d = Path(td) / outro
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_text((RAIZ / outro).read_text(encoding='utf-8'))
        mau, quais, _ = confere(td)
        assert not mau and any('tem 2 ' in x for x in quais), \
            '⛔ NAO pega o controle encolhido para 2: %s' % quais
    print('  autoteste ✅ (o controle de 42 reduzido a 2 REPROVA nominalmente)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, faltas, vistos = confere()
    print('  %d contagens conferidas contra o que o artigo supoe' % vistos)
    for x in faltas:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
