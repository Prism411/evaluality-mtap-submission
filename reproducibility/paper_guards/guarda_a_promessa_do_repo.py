#!/usr/bin/env python3
"""⛔ A DISPONIBILIDADE QUE O ARTIGO PROMETE EXISTE DE FATO?

POR QUE EXISTE (08/09/2026). A secao *Data availability* diz que scripts, escores derivados,
clusters, anotacoes, sementes e latencias «are released at a tagged version of the
repository», e *Code availability* nomeia a URL. Conferi: o repositorio **nao tem nenhuma
tag** e esta **54 commits a frente do remoto**. A promessa e verificavel e nao estava
cumprida — e nenhuma guarda olhava, porque todas olham o conteudo cientifico.

⚠️ Isto NAO e um defeito do texto: e uma pendencia de ACAO do autor, e a guarda existe para
que ela nao chegue calada a submissao. Por isso ela sai com codigo 3 («aguardando o autor»)
em vez de reprovar: enviar e publicar sao decisoes de quem assina.

Autoteste de duas pernas: um estado com tag e sincronizado passa; sem tag, ou com commit
nao enviado, e sinalizado.
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
REPO = Path('/dados/Projetos/evaluality-mtap-submission')
CORPO = ['main.tex']


def promete_tag(textos=None):
    t = textos if textos is not None else '\n'.join(
        (AQUI / f).read_text(encoding='utf-8') for f in CORPO if (AQUI / f).exists())
    return bool(re.search(r'tagged version of the repository|at a tagged release', t, re.I))


def estado(repo=None):
    repo = repo or REPO
    if not repo.exists():
        return None

    def g(*a):
        r = subprocess.run(['git', '-C', str(repo)] + list(a), capture_output=True, text=True)
        return r.stdout.strip()

    tags = [x for x in g('tag').split('\n') if x]
    frente = g('rev-list', '--count', 'origin/main..main') or '0'
    return {'tags': tags, 'nao_enviados': int(frente)}


def confere(textos=None, est=None):
    est = est if est is not None else estado()
    if est is None:
        return None, ['o repositorio nao esta em %s' % REPO]
    pend = []
    if promete_tag(textos) and not est['tags']:
        pend.append('o corpo promete «a tagged version» e o repositorio nao tem nenhuma tag')
    if est['nao_enviados']:
        pend.append('%d commit(s) ainda nao enviados ao remoto que o corpo nomeia'
                    % est['nao_enviados'])
    return not pend, pend


def autoteste():
    bom = {'tags': ['v1.0-submission'], 'nao_enviados': 0}
    ok, _ = confere(textos='released at a tagged version of the repository', est=bom)
    if not ok:
        print('    ⛔ autoteste: sinalizou um estado que ja cumpre a promessa')
        return False
    for ruim, nome in ((({'tags': [], 'nao_enviados': 0}), 'sem tag'),
                       (({'tags': ['v1'], 'nao_enviados': 3}), 'com commit nao enviado')):
        ok2, _ = confere(textos='released at a tagged version of the repository', est=ruim)
        if ok2:
            print('    ⛔ autoteste: nao sinalizou o estado %s' % nome)
            return False
    # ⚠️ e a perna que impede alarme falso: se o corpo NAO prometer tag, a falta de tag
    # nao e pendencia nenhuma
    ok3, p3 = confere(textos='the archive accompanies the submission', est={'tags': [], 'nao_enviados': 0})
    if not ok3:
        print('    ⛔ autoteste: cobrou tag de um corpo que nao promete tag: %s' % p3)
        return False
    print('   autoteste ✅ (sinaliza sem tag e nao enviado; nao cobra tag de quem nao promete)')
    return True


if __name__ == '__main__':
    if not autoteste():
        sys.exit(1)
    r = confere()
    if r[0] is None:
        print('  ⏳ %s' % r[1][0])
        sys.exit(3)
    ok, pend = r
    if ok:
        print('  ✅ a disponibilidade que o corpo promete esta cumprida no repositorio')
        sys.exit(0)
    print('  ⏳ aguardando o autor: a promessa de disponibilidade ainda nao esta cumprida')
    for p in pend:
        print('    ⬜ %s' % p)
    sys.exit(3)
