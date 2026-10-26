#!/usr/bin/env python3
"""⛔ O QUE O CLONE PRODUZ E O QUE O ARTIGO IMPRIME?

POR QUE EXISTE (09/09/2026). A guarda 28 prova que os scripts do pacote RODAM de um clone.
Nao prova o que importa: que eles produzem os MESMOS numeros que o artigo publica. Rodar
sem erro e barato; reconstruir a estatistica reportada e a promessa da secao *Data
availability*.

⭐ COMO SEPARA: clona o repositorio, cega os caminhos da maquina do autor, roda cada script
declarado LA DENTRO, le o JSON que ele acabou de gravar no clone, deriva o valor pela mesma
regra do gerador de macros, e compara com o que o `regras_publicadas.tex` do artigo imprime.
Se o pacote estiver incompleto ou desatualizado, os numeros divergem e isso aparece.

⚠️ Sao os numeros que o CORPO imprime, nao os que o JSON guarda: a derivacao (somar celulas,
tirar mediana, arredondar) faz parte do que precisa reproduzir.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).parent
REPO = Path('/data/projects/submission-package')
PY_ = '/data/projects/pipeline/.venv/bin/python'
LOCAIS = ['/data/projects/benchmark',
          '/home/user/workspace/07-Artigos/manuscript',
          '/data/projects/submission-package/reproducibility/derived_data']

# macro impressa -> (script que a produz, arquivo gravado, como derivar do JSON)
ALVOS = {
    'invCelulas': ('quantas_invertem_ALEM_DO_ACASO.py', 'quantas_invertem_ALEM_DO_ACASO.json',
                   lambda d: str(sum(len(v['tipos_abaixo_de_50']) for v in d['por_operacao'].values()))),
    'invTestes': ('quantas_invertem_ALEM_DO_ACASO.py', 'quantas_invertem_ALEM_DO_ACASO.json',
                  lambda d: str(d['n_testes'])),
    'subPct': ('a_substituicao_concorda_acima_do_acaso.py',
               'a_substituicao_concorda_acima_do_acaso.json',
               lambda d: '%.1f' % d['por_linha']['liqe_x_implantada']['pct']),
    'claPar': ('a_classe_nao_concorda_consigo.py', 'a_classe_nao_concorda_consigo.json',
               lambda d: ('%.3f' % d['kappa_par_a_par_entre_operacoes']['mediana']).replace('0.', '.')),
    'tipMediana': ('a_implantada_e_tipica_da_classe.py', 'a_implantada_e_tipica_da_classe.json',
                   lambda d: '%.1f' % d['classe_de_sumarizacao']['mediana']),
    'excMediana': ('as_tres_excecoes_do_mecanismo.py', 'as_tres_excecoes_do_mecanismo.json',
                   lambda d: ('%d' % d['n_desc_medida']['mediana']).replace('1092', '1{,}092')),
}


def macros(texto=None):
    t = texto if texto is not None else (AQUI / 'regras_publicadas.tex').read_text(encoding='utf-8')
    return {m.group(1): m.group(2)
            # ⚠️ um nivel de chave aninhada: o valor `1{,}092` quebrava a versao
            # anterior, que parava na primeira chave interna
            for m in re.finditer(r'\\newcommand\{\\([a-zA-Z]+)\}\{((?:[^{}]|\{[^{}]*\})*)\}', t)}


def confere(alvos=None, mac=None):
    alvos = ALVOS if alvos is None else alvos
    mac = macros() if mac is None else mac
    if not REPO.exists():
        return None, ['o repositorio nao esta em %s' % REPO], 0
    ruins, n = [], 0
    with tempfile.TemporaryDirectory() as td:
        alvo = Path(td) / 'clone'
        if subprocess.run(['git', 'clone', '-q', str(REPO), str(alvo)],
                          capture_output=True).returncode:
            return False, ['git clone falhou'], 0
        rep = alvo / 'reproducibility'
        for f in rep.glob('*.py'):
            t = f.read_text(encoding='utf-8', errors='ignore')
            novo = t
            for i, loc in enumerate(LOCAIS):
                novo = novo.replace("'%s'" % loc, "'/nao/existe%d'" % i)
            if novo != t:
                f.write_text(novo, encoding='utf-8')
        feitos = set()
        for nome, (script, saida, deriva) in alvos.items():
            if script not in feitos:
                r = subprocess.run([PY_, script], cwd=rep, capture_output=True, text=True,
                                   timeout=300)
                feitos.add(script)
                if r.returncode:
                    ruins.append('%s nao rodou no clone' % script)
                    continue
            p = rep / saida
            if not p.exists():
                ruins.append('%s nao gravou %s' % (script, saida))
                continue
            n += 1
            obtido = deriva(json.loads(p.read_text(encoding='utf-8')))
            impresso = mac.get(nome)
            if impresso != obtido:
                ruins.append('\\%s: o artigo imprime %r e o clone produz %r'
                             % (nome, impresso, obtido))
    return not ruins, ruins, n


def autoteste():
    ok, ruins, n = confere()
    if not ok:
        print('    ⛔ autoteste: o clone ja nao reproduz: %s' % ruins[:2])
        return False
    # ⛔ a perna que separa: um valor impresso diferente TEM de ser acusado
    mac = macros()
    mac = dict(mac, invCelulas='34')
    ok2, r2, _ = confere({'invCelulas': ALVOS['invCelulas']}, mac)
    if ok2:
        print('    ⛔ autoteste: aprovou um valor impresso que o clone nao produz')
        return False
    print('   autoteste ✅ (%d numeros conferidos; valor trocado REPROVA)' % n)
    return True


if __name__ == '__main__':
    if not REPO.exists():
        print('  ⏳ o repositorio de submissao nao esta aqui: nao aprova nem reprova')
        sys.exit(3)
    if not autoteste():
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d numeros do artigo reproduzidos rodando o pacote de um clone cego' % n)
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
