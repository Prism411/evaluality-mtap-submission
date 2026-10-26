#!/usr/bin/env python3
"""⛔ QUEM CLONAR O REPOSITORIO CONSEGUE COMPILAR OS DOIS DOCUMENTOS?

POR QUE EXISTE (08/09/2026). O README promete `cd paper && latexmk -pdf main.tex` e o mesmo
para o suplemento. **Isso nunca tinha sido testado a partir de um clone.** Quando testei, o
corpo compilava e o **suplemento saia com 69 citacoes indefinidas e uma pagina a menos**: o
`references.bib` so existia em `paper/`, e o `supplementary.tex` o pede na propria pasta.

⚠️ Compilar na pasta de trabalho NAO testa isso: la o arquivo esta presente por acaso. So um
clone limpo, num diretorio temporario, prova a promessa.

Autoteste de duas pernas: o clone atual compila os dois; e um clone com o `references.bib`
do suplemento removido REPROVA.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path('/data/projects/submission-package')
DOCS = [('paper', 'main'), ('supplement', 'supplementary')]


def compila(raiz, pasta, doc):
    d = raiz / pasta
    for cmd in (['pdflatex', '-interaction=nonstopmode', doc + '.tex'],
                ['bibtex', doc],
                ['pdflatex', '-interaction=nonstopmode', doc + '.tex'],
                ['pdflatex', '-interaction=nonstopmode', doc + '.tex']):
        subprocess.run(cmd, cwd=d, capture_output=True)
    log = (d / (doc + '.log'))
    if not log.exists():
        return None, None, None
    txt = log.read_text(errors='ignore')
    erros = sum(1 for l in txt.split('\n') if l.startswith('! '))
    indef = len(re.findall(r'(?:Reference|Citation) `[^\']*\' on page \d+ undefined', txt))
    pdf = d / (doc + '.pdf')
    pags = None
    if pdf.exists():
        out = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
        for l in out.split('\n'):
            if l.lower().startswith('pages'):
                pags = int(l.split()[-1])
    return erros, indef, pags


def confere(remover=None):
    if not REPO.exists():
        return False, ['o repositorio nao esta neste disco'], {}, []
    with tempfile.TemporaryDirectory() as td:
        alvo = Path(td) / 'repo'
        r = subprocess.run(['git', 'clone', '-q', str(REPO), str(alvo)], capture_output=True)
        if r.returncode:
            return False, ['git clone falhou'], {}, []
        sujo = subprocess.run(['git', 'status', '--porcelain'], cwd=str(REPO),
                              capture_output=True, text=True).stdout.strip()
        if sujo:
            n = len(sujo.split('\n'))
            ruins_pendentes = ['⚠️ %d arquivo(s) alterado(s) e NAO commitado(s): o clone '
                               'compila o ultimo commit, nao o que esta sincronizado' % n]
        else:
            ruins_pendentes = []
        if remover:
            p = alvo / remover
            if p.exists():
                p.unlink()
        ruins, res = [], {}
        avisos = list(ruins_pendentes)
        for pasta, doc in DOCS:
            e, i, pg = compila(alvo, pasta, doc)
            res[pasta] = (e, i, pg)
            if e is None:
                ruins.append('%s: nao gerou log' % pasta)
            else:
                if e:
                    ruins.append('%s: %d erro(s) de compilacao' % (pasta, e))
                if i:
                    ruins.append('%s: %d remissao/citacao indefinida' % (pasta, i))
                if not pg:
                    ruins.append('%s: nao gerou PDF' % pasta)
        return not ruins, ruins, res, avisos


def _autoteste():
    ok, ruins, res, avisos = confere()
    assert ok, '⛔ o clone atual ja nao compila: %s' % ruins
    # o mundo errado: o defeito real de 08/09
    ok2, ruins2, _, _ = confere(remover='supplement/references.bib')
    assert not ok2, '⛔ NAO separa: sem o references.bib do suplemento ainda passou'
    print('  autoteste ✅ (sem o references.bib do suplemento, o clone REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins, res, avisos = confere()
    for a in avisos:
        print('  %s' % a)
    for pasta, (e, i, pg) in res.items():
        print('  %-12s %s paginas, %s erro(s), %s indefinida(s)' % (pasta, pg, e, i))
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA: um clone limpo compila os dois' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
