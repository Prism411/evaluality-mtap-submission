#!/usr/bin/env python3
"""⛔ O GERADOR PUBLICADO PRODUZ A TABELA PUBLICADA?

POR QUE EXISTE (14/09/2026). Em 13/09 eu sincronizei `paper/` e `supplement/` do repositorio
de submissao e ESQUECI `reproducibility/paper_generators/`. O resultado: o suplemento trazia
a Tabela S30 com duas colunas de generalizacao e o gerador distribuido com o mesmo nome
ainda tinha UMA, e a linha antiga que misturava media-z com ridge.

⚠️ Um revisor abriu os dois e viu. A rota de reproducao que o artigo promete ficou falsa
sem que nada quebrasse: os PDFs estavam certos, o codigo ao lado nao os produzia.

⭐ ONZE geradores estavam defasados, nao um. Copiar a mao nao escala, e esquecer um diretorio
nao deixa rastro. Esta guarda compara byte a byte o que o pacote usa com o que o repositorio
publica, e reprova nominalmente.

Autoteste de duas pernas: o estado atual passa, e um gerador alterado REPROVA.
"""
import shutil
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).parent
REPO = Path('/data/projects/submission-package')
PARES = [('gera_*.py', REPO / 'reproducibility/paper_generators'),
         ('guarda_*.py', REPO / 'reproducibility/paper_guards')]


def confere(aqui=None, repo_dirs=None):
    aqui = Path(aqui) if aqui else AQUI
    pares = repo_dirs or PARES
    faltam, diferem, vistos = [], [], 0
    for padrao, destino in pares:
        if not Path(destino).exists():
            faltam.append('%s: diretorio ausente' % destino)
            continue
        for f in sorted(aqui.glob(padrao)):
            alvo = Path(destino) / f.name
            vistos += 1
            if not alvo.exists():
                faltam.append(f.name)
            elif f.read_bytes() != alvo.read_bytes():
                diferem.append(f.name)
    assert vistos, '⛔ nenhum script comparado: a guarda aprovaria no vacuo'
    return (not faltam and not diferem), faltam, diferem, vistos


def _autoteste():
    ok, fa, di, _ = confere()
    assert ok, '⛔ o estado atual deveria passar: faltam=%s diferem=%s' % (fa[:2], di[:2])
    # ⭐ o mundo errado e o defeito REAL: um gerador publicado com conteudo antigo
    with tempfile.TemporaryDirectory() as td:
        g = Path(td) / 'paper_generators'
        g.mkdir()
        nomes = sorted(AQUI.glob('gera_*.py'))
        assert nomes, '⛔ nao ha gerador para montar o mundo errado'
        for f in nomes:
            shutil.copy2(f, g / f.name)
        (g / nomes[0].name).write_text('# versao antiga\n')
        mau, _fa, dif, _ = confere(repo_dirs=[('gera_*.py', g)])
        assert not mau and nomes[0].name in dif, \
            '⛔ NAO pega um gerador publicado desatualizado'
        # e um ausente tambem
        (g / nomes[0].name).unlink()
        mau2, falta, _d, _ = confere(repo_dirs=[('gera_*.py', g)])
        assert not mau2 and nomes[0].name in falta, '⛔ NAO pega um gerador ausente'
    print('  autoteste ✅ (gerador desatualizado e gerador ausente REPROVAM)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, faltam, diferem, vistos = confere()
    print('  %d script(s) do pacote comparados com o repositorio publicado' % vistos)
    for x in faltam:
        print('    ⛔ nao publicado: %s' % x)
    for x in diferem:
        print('    ⛔ publicado com conteudo DIFERENTE: %s' % x)
    print('  %s' % ('✅ APROVA: o repositorio publica o que o pacote usa'
                    if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
