#!/usr/bin/env python3
"""⛔ O MESMO ARTIGO ENTRA DUAS VEZES NA CONTAGEM DO ACERVO?

POR QUE EXISTE (28/09/2026). `jeong2016static.pdf` e `jeong2017static.pdf` eram o MESMO
arquivo (md5 igual, EURASIP JIVP 2017) sob dois citekeys, e a varredura por termo os contava
como dois sumarizadores: a Tabela 1 dizia 86 trabalhos e 51/40/1/24, quando eram 85 e
50/39/1/23. A varredura nao tem como perceber isso, porque ela le TEXTO, e dois nomes com o
mesmo texto sao, para ela, dois trabalhos. Sugestao do `@agente-iqa`; escrita pelo
`@agente-iqa-cli-3`.

O que a guarda afirma, sobre o retrato que o artigo usa (`taxonomia_das_classes.json`):
  1. nenhum md5 se repete entre os PDF contados;
  2. o `n_sumarizadores` gravado e o que a lista `por_pdf` da quando se conta;
  3. o `classes_contra_o_testbed.json`, que alimenta a Tabela 1, usa o MESMO denominador.

⚠️ Os PDF moram no `library`, que nao vai no pacote. Num clone sem ele a perna 1 nao
tem como rodar, e a guarda DIZ isso em vez de aprovar calada; as pernas 2 e 3 rodam sempre.

Autoteste: plantar um segundo nome com o md5 de um PDF ja contado REPROVA.
"""
import hashlib
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from caminho_dos_dados import DADOS as QB   # noqa: E402

ACERVO = Path('/home/user/workspace/library/papers')


def duplicados(md5_por_nome):
    grupos = {}
    for nome, h in md5_por_nome.items():
        grupos.setdefault(h, []).append(nome)
    return [sorted(v) for v in grupos.values() if len(v) > 1]


def _autoteste(md5_por_nome):
    """Planta sobre uma base SEM repeticao, para que um defeito real apareca na mensagem da
    guarda e nao como falha do autoteste."""
    base = {}
    for nome, h in sorted(md5_por_nome.items()):
        if h not in base.values():
            base[nome] = h
    assert not duplicados(base), 'a base do autoteste deveria estar limpa'
    nome, h = next(iter(base.items()))
    plantado = dict(base, **{'copia_de_' + nome: h})
    assert duplicados(plantado), '⛔ um md5 repetido plantado NAO reprovou: guarda morta'


def main():
    tx = json.load(open(QB / 'taxonomia_das_classes.json'))
    cl = json.load(open(QB / 'classes_contra_o_testbed.json'))
    por_pdf = tx['por_pdf']
    falhas = []

    # perna 2: o numero gravado e o que a lista da
    n_lista = sum(1 for v in por_pdf.values() if v['e_sumarizador'])
    if tx['n_sumarizadores'] != n_lista:
        falhas.append(f'n_sumarizadores gravado {tx["n_sumarizadores"]} != contado {n_lista}')
    # perna 3: a Tabela 1 usa o mesmo denominador
    if cl['n_sumarizadores'] != n_lista:
        falhas.append(f'classes_contra_o_testbed usa {cl["n_sumarizadores"]}, a lista da {n_lista}')

    # perna 1: md5
    if not ACERVO.exists():
        print(f'  ⚠️ acervo ausente ({ACERVO}): a perna do md5 NAO rodou neste ambiente')
    else:
        faltam = [n for n in por_pdf if not (ACERVO / n).exists()]
        if faltam:
            falhas.append(f'{len(faltam)} PDF do retrato sumiram do acervo: {faltam[:3]}')
        md5 = {n: hashlib.md5((ACERVO / n).read_bytes()).hexdigest()
               for n in por_pdf if (ACERVO / n).exists()}
        _autoteste(md5)
        print('  autoteste ✅ (um md5 repetido plantado REPROVA)')
        for g in duplicados(md5):
            falhas.append(f'mesmo arquivo contado {len(g)} vezes: {g}')
        print(f'  {len(md5)} PDF do retrato conferidos por md5')

    print(f'  {n_lista} sumarizadores no retrato; a Tabela 1 usa {cl["n_sumarizadores"]}')
    if falhas:
        for f in falhas:
            print('  ⛔ ' + f)
        print('  ⛔ REPROVA')
        return 1
    print('  ✅ APROVA: nenhum artigo contado duas vezes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
