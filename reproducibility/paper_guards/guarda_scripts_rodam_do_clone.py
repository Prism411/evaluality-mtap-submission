#!/usr/bin/env python3
"""⛔ OS SCRIPTS DE ANALISE RODAM A PARTIR DO PACOTE, OU SO NA MAQUINA DO AUTOR?

POR QUE EXISTE (08/09/2026). O `guarda_repo_compila_do_zero.py` prova que um clone COMPILA
os dois documentos. Nao prova nada sobre as ANALISES: quatro scripts que escrevi hoje foram
para o pacote com `Path('/dados/Projetos/quality-benchmark')` cravado, e nesse estado o
pacote traz um script que so roda aqui. A promessa de replicacao fica sem lastro, e ninguem
descobre ate alguem de fora tentar.

⭐ COMO SEPARA: clona o repositorio num diretorio temporario, **apaga os caminhos da maquina
do autor** trocando-os por caminhos inexistentes, e roda cada script declarado. Se algum
depender de algo que o pacote nao traz, ele quebra — que e exatamente o que se quer saber.

⚠️ E foi assim que apareceu que o `ops_da_literatura.py`, o modulo que IMPLEMENTA as
dezesseis operacoes, nao estava no pacote. O artefato mais util para quem quer conferir a
auditoria estava de fora, e nenhuma checagem via.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path('/dados/Projetos/evaluality-mtap-submission')
PY_ = '/dados/Projetos/jl-summ-graph/.venv/bin/python'
# os caminhos da maquina do autor que o clone NAO pode precisar
LOCAIS = ['/dados/Projetos/quality-benchmark',
          '/home/jader/memoria-agentes/07-Artigos/evaluality-literatura',
          '/dados/Projetos/evaluality-mtap-submission/reproducibility/derived_data']
SCRIPTS = ['a_substituicao_concorda_acima_do_acaso.py',
           'quantas_invertem_ALEM_DO_ACASO.py',
           'as_tres_excecoes_do_mecanismo.py',
           'a_evidencia_da_fonte_preve_a_falha.py']


def confere(scripts=None, cegar=True):
    scripts = scripts if scripts is not None else SCRIPTS
    if not REPO.exists():
        return None, ['o repositorio nao esta em %s' % REPO], 0
    ruins = []
    with tempfile.TemporaryDirectory() as td:
        alvo = Path(td) / 'clone'
        r = subprocess.run(['git', 'clone', '-q', str(REPO), str(alvo)], capture_output=True)
        if r.returncode:
            return False, ['git clone falhou'], 0
        rep = alvo / 'reproducibility'
        if cegar:
            for f in rep.glob('*.py'):
                t = f.read_text(encoding='utf-8', errors='ignore')
                novo = t
                for i, loc in enumerate(LOCAIS):
                    novo = novo.replace("'%s'" % loc, "'/nao/existe%d'" % i)
                if novo != t:
                    f.write_text(novo, encoding='utf-8')
        for s in scripts:
            if not (rep / s).exists():
                ruins.append('%s nao esta no pacote' % s)
                continue
            r = subprocess.run([PY_, s], cwd=rep, capture_output=True, text=True, timeout=300)
            if r.returncode:
                erro = [l for l in (r.stderr or '').strip().split('\n') if 'Error' in l]
                ruins.append('%s: %s' % (s, erro[-1][:90] if erro else 'saiu com erro'))
    return not ruins, ruins, len(scripts)


def autoteste():
    """⚠️ As duas pernas. A que separa e a do caminho CEGADO: sem cegar, o script acha os
    dados na maquina do autor e passa mesmo faltando no pacote — foi o meu primeiro teste,
    e ele aprovava um pacote quebrado."""
    ok, ruins, _ = confere()
    if not ok:
        print('    ⛔ autoteste: o pacote atual ja nao roda: %s' % ruins[:2])
        return False
    # ⛔ um script que o pacote nao traz TEM de reprovar
    ok2, _, _ = confere(scripts=['nao_existe_no_pacote.py'])
    if ok2:
        print('    ⛔ autoteste: aprovou um script ausente do pacote')
        return False
    print('   autoteste ✅ (com os caminhos do autor cegados; script ausente REPROVA)')
    return True


if __name__ == '__main__':
    if not REPO.exists():
        print('  ⏳ o repositorio de submissao nao esta aqui: nao aprova nem reprova')
        sys.exit(3)
    if not autoteste():
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d script(s) de analise rodados de um clone, sem os caminhos do autor' % n)
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
