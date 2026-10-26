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
REPO = Path('/data/projects/submission-package')
CORPO = ['main.tex']


def promete_tag(textos=None):
    t = textos if textos is not None else '\n'.join(
        (AQUI / f).read_text(encoding='utf-8') for f in CORPO if (AQUI / f).exists())
    # ⚠️ 28/09 (cli-3): o texto dizia «the tagged version named under Code availability» e
    # esta regra nao casava: a guarda nao via a promessa. Agora casa as tres redacoes.
    return bool(re.search(r'tagged version of the repository|at a tagged release|'
                          r'the tagged version named', t, re.I))


def tag_nomeada(textos=None):
    """⭐ 28/09: a tag que o Code availability NOMEIA. Existir alguma tag nao basta: as tags do
    repositorio eram de 13 a 15/09, anteriores a toda a revisao de 27/09."""
    t = textos if textos is not None else '\n'.join(
        (AQUI / f).read_text(encoding='utf-8') for f in CORPO if (AQUI / f).exists())
    m = re.search(r'tag \\texttt\{([^}]+)\}', t)
    return m.group(1).replace('\\', '') if m else None


def estado(repo=None):
    repo = repo or REPO
    if not repo.exists():
        return None

    def g(*a):
        r = subprocess.run(['git', '-C', str(repo)] + list(a), capture_output=True, text=True)
        return r.stdout.strip()

    tags = [x for x in g('tag').split('\n') if x]
    frente = g('rev-list', '--count', 'origin/main..main') or '0'
    nomeada = tag_nomeada()
    sujo = bool(g('status', '--porcelain'))
    no_head = bool(nomeada) and nomeada in tags and g('rev-parse', nomeada + '^{commit}') == g('rev-parse', 'HEAD')
    return {'tags': tags, 'nao_enviados': int(frente), 'nomeada': nomeada,
            'nomeada_no_head': no_head, 'arvore_suja': sujo}


def confere(textos=None, est=None):
    est = est if est is not None else estado()
    if est is None:
        return None, ['o repositorio nao esta em %s' % REPO]
    pend = []
    if promete_tag(textos) and not est['tags']:
        pend.append('o corpo promete «a tagged version» e o repositorio nao tem nenhuma tag')
    nom = est.get('nomeada')
    if nom and nom not in est['tags']:
        pend.append('o Code availability nomeia a tag %s, que nao existe no repositorio' % nom)
    elif nom and not est.get('nomeada_no_head', True):
        pend.append('a tag %s nao aponta para o HEAD: a versao publicada nao e a atual' % nom)
    if est.get('arvore_suja'):
        pend.append('o repositorio tem alteracoes nao commitadas')
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
    # ⭐ 28/09: existir tag antiga nao cumpre a promessa de uma tag NOMEADA que nao existe
    ok4, _ = confere(textos='the tagged version named under Code availability',
                     est={'tags': ['submission-2026-09-15'], 'nao_enviados': 0,
                          'nomeada': 'submission-2099-01-01', 'nomeada_no_head': False,
                          'arvore_suja': False})
    if ok4:
        print('    ⛔ autoteste: aprovou uma tag nomeada que nao existe')
        return False
    print('   autoteste ✅ (sinaliza sem tag, nao enviado e tag nomeada ausente; nao cobra tag de quem nao promete)')
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
