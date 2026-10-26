#!/usr/bin/env python3
r"""⛔ RODAR O MESMO GERADOR DUAS VEZES DA O MESMO ARQUIVO?

POR QUE EXISTE (15/09/2026). `gera_fig_direcao.py` e `gera_fig_inversao.py` iteravam sobre um
`set`, e a ordem de um `set` de strings muda entre execucoes do Python pelo hash randomizado.
O `.tex` saia com os mesmos pontos em ORDEM diferente a cada corrida.

🔴 A figura era a mesma, entao nada no PDF denunciava. Mas o ARQUIVO nao era reproduzivel —
e o arquivo e o que o repositorio promete. O sintoma foi indireto: eu sincronizava o pacote,
a suite regerava, e a guarda de versao unica acusava «difere do publicado» **numa corrida
que nao mudou nada**.

⭐ A regra: gerar duas vezes seguidas tem de dar arquivos identicos byte a byte. ⚠️ Rodar em
processos SEPARADOS e essencial: dentro de um mesmo interpretador o hash e estavel e a
verificacao passaria sem exercitar nada.
"""
import hashlib, os, subprocess, sys
from pathlib import Path

A = Path(__file__).parent
PY = sys.executable


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def saida_de(gerador):
    """O `.tex` que este gerador escreve, pelo nome: gera_fig_x.py -> fig_x.tex"""
    nome = gerador.stem.replace('gera_', '', 1)
    for cand in (A / (nome + '.tex'), A / (nome.replace('tabela_', 'tab_') + '.tex')):
        if cand.exists():
            return cand
    return None


def instaveis(geradores=None):
    ruins = []
    for g in (geradores or sorted(A.glob('gera_fig_*.py')) + sorted(A.glob('gera_tab*.py'))):
        alvo = saida_de(g)
        if alvo is None:
            # pode ser a primeira geracao: roda uma vez e procura de novo
            subprocess.run([PY, str(g)], cwd=str(A), capture_output=True)
            alvo = saida_de(g)
        if alvo is None:
            continue
        # ⚠️ cada corrida num processo NOVO, com semente de hash diferente: e o unico jeito
        #    de exercitar a ordem de `set`.
        assinaturas = []
        for semente in ('1', '2'):
            env = dict(os.environ, PYTHONHASHSEED=semente)
            r = subprocess.run([PY, str(g)], cwd=str(A), capture_output=True, env=env)
            if r.returncode:
                ruins.append('%s falhou ao rodar' % g.name)
                break
            assinaturas.append(sha(alvo))
        if len(assinaturas) == 2 and assinaturas[0] != assinaturas[1]:
            ruins.append('%s -> %s muda entre execucoes (ordem de conjunto?)'
                         % (g.name, alvo.name))
    return ruins


def main():
    r = instaveis()
    for x in r:
        print('  ⛔ %s' % x)
    if not r:
        n = len([g for g in sorted(A.glob('gera_*.py')) if saida_de(g)])
        print('  ✅ os %d geradores com saida .tex sao deterministicos sob duas sementes' % n)
    return 1 if r else 0


def autoteste():
    mal = 0
    n = len(instaveis())
    print(f"  {'✅' if n == 0 else '⛔'} estado atual: {n} gerador(es) instavel(eis), esperado 0")
    mal += n != 0
    # ⛔ o defeito real replantado, num gerador de mentira
    teste = A / 'gera_instavel_para_teste.py'
    saida = A / 'instavel_para_teste.tex'
    teste.write_text(
        "from pathlib import Path\n"
        "S = {'alfa', 'beta', 'gama', 'delta', 'epsilon', 'zeta', 'eta'}\n"
        "Path(__file__).parent.joinpath('instavel_para_teste.tex').write_text(\n"
        "    '\\n'.join(S) + '\\n')\n")
    try:
        n = len(instaveis([teste]))
        print(f"  {'✅' if n == 1 else '⛔'} gerador que itera sobre set: {n}, esperado 1")
        mal += n != 1
    finally:
        teste.unlink(missing_ok=True)
        saida.unlink(missing_ok=True)
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
