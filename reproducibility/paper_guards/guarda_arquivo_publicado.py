#!/usr/bin/env python3
"""⛔ TUDO QUE PRODUZ UM NUMERO DO ARTIGO ESTA NO REPOSITORIO PROMETIDO?

POR QUE EXISTE (08/09/2026). A declaracao de disponibilidade promete que «scripts, derived
scores, clusters, annotations, seeds and latency results are released at a tagged version of
the repository». Em 08/09 essa frase era **falsa**: o ultimo commit do
`evaluality-mtap-submission` era de 24/08 e **19 dos 20 arquivos de dados que os geradores
leem hoje nao estavam la** — inclusive todos os que sustentam a tabela de sintese e a
leitura documental das fontes.

Nada disso gera erro de compilacao. A promessa e prosa, e prosa nao tem guarda.

⚠️ PUBLICAR E DECISAO DO AUTOR, entao esta guarda sai com codigo 3 (aguarda o autor) e nao
com 1 (defeito). Ela produz a lista e o comando; quem aperta o botao e o Jader.
"""
import glob
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
QB = Path('/dados/Projetos/quality-benchmark')
REPO = Path('/dados/Projetos/evaluality-mtap-submission')
MANIFESTO = AQUI / 'artefatos_que_o_artigo_le.json'


def dependencias():
    """Todo .json que algum gerador ou guarda deste artigo abre."""
    dep = set()
    for f in sorted(glob.glob(str(AQUI / 'gera_*.py')) + glob.glob(str(AQUI / 'guarda_*.py'))):
        t = io.open(f, encoding='utf-8').read()
        for m in re.finditer(r"['\"]([A-Za-z0-9_./-]+\.json)['\"]", t):
            b = os.path.basename(m.group(1))
            if (QB / b).exists():
                dep.add(b)
    return sorted(dep)


def publicados():
    if not REPO.exists():
        return None
    out = subprocess.run(['git', 'ls-files'], cwd=REPO, capture_output=True, text=True)
    return {os.path.basename(x) for x in out.stdout.split()}


def confere():
    dep = dependencias()
    pub = publicados()
    if pub is None:
        return False, dep, 'o repositorio prometido nao esta neste disco'
    return sorted(set(dep) - pub) == [], sorted(set(dep) - pub), None


def _autoteste():
    dep = dependencias()
    assert dep, '⛔ zero dependencias lidas: aprovaria no vacuo'
    assert all((QB / d).exists() for d in dep), '⛔ listou arquivo que nao existe'
    # o mundo errado: um repositorio que nao contem nada
    faltam = sorted(set(dep) - set())
    assert faltam, '⛔ NAO separa: um repo vazio nao acusaria nada'
    print('  autoteste ✅ (%d dependencias lidas; repo vazio acusaria todas)' % len(dep))
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, faltam, erro = confere()
    dep = dependencias()
    MANIFESTO.write_text(json.dumps(
        {'_o_que_e': 'todo arquivo de dados que os geradores e guardas deste artigo leem',
         'n': len(dep), 'arquivos': dep, 'faltam_no_repositorio': faltam},
        ensure_ascii=False, indent=1), encoding='utf-8')
    print('  %d arquivos de dados sustentam numeros do artigo' % len(dep))
    if erro:
        print('  ⛔ %s' % erro)
        sys.exit(1)
    if ok:
        print('  ✅ APROVA: todos estao no repositorio prometido')
        sys.exit(0)
    print('  ⏳ %d ainda nao publicados (lista em %s):' % (len(faltam), MANIFESTO.name))
    for x in faltam[:8]:
        print('      %s' % x)
    if len(faltam) > 8:
        print('      ... e mais %d' % (len(faltam) - 8))
    print('  ⏳ AGUARDA O AUTOR: copiar para %s e commitar e decisao do Jader.' % REPO.name)
    print('     cp %s/{%s} %s/' % (QB, ','.join(faltam[:3]) + ',...', REPO))
    sys.exit(3)
