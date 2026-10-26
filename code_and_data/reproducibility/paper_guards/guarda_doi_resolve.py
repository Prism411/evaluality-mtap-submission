#!/usr/bin/env python3
"""⛔ CADA DOI DO .BIB APONTA PARA O ARTIGO QUE A ENTRADA DIZ SER?

POR QUE EXISTE (08/09/2026). Um DOI errado passa por tudo: o LaTeX compila, a bibliografia
imprime, e a citacao parece perfeita. So quem CLICA descobre. Encontrei quatro:

  ⛔ `wu2024qinstruct`  .02412 apontava para «Navigating Beyond Dropout»
  ⛔ `ye2024mplugowl2`  .01238 apontava para «Pixel Aligned Language Models»
  ⛔ `moraes2022subjectivity`  DOI da [venue] dava 404; o certo e o da ACM
  ⛔ `huang2023xgcvqa`  DOI dava 404, E o local estava errado (BMSB, e ICMEW)

Os dois primeiros erravam UM DIGITO e caiam noutro artigo do mesmo proceedings. Esse e o
pior caso: plausivel, do ano certo, da conferencia certa, e completamente errado.

⚠️ Precisa de rede. Sem rede, a guarda AVISA e nao reprova — uma checagem que nao rodou nao
pode dizer ✅.
"""
import io
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
# ⚠️ conferidos a mao e CERTOS: o titulo no .bib difere do registro por motivo declarado
# ⚠️ «ACL» e a sigla da Association for Computational Linguistics, escrita por extenso
# no registro; a sigla nao aparece literal.
LOCAL_ACEITO = {
    'fabbri2019multinews': 'ACL e a sigla da Association for Computational Linguistics, '
                           'escrita por extenso no registro',
    'hasler2003colorfulness': 'o registro traz apenas «SPIE Proceedings»; o nome do '
                              'volume, «Human Vision and Electronic Imaging», nao esta la',
}

ACEITOS = {
    'barbieri2021tese': 'o .bib traz o titulo em ingles; o registro da USP esta em portugues',
    'sarmento2024sumarizacao': 'idem, titulo em portugues no registro',
    'ye2024mplugowl2': 'o registro do IEEE grafa «OwI2» com i maiusculo',
    'hasler2003colorfulness': 'o registro traz o titulo curto da SPIE',
}


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def entradas():
    b = (AQUI / 'references.bib').read_text(encoding='utf-8')
    out = {}
    for k, c in re.findall(r'@\w+\{([^,]+),(.*?)\n\}', b, re.S):
        d = re.search(r'doi\s*=\s*[{"]([^}"]+)', c)
        t = re.search(r'title\s*=\s*[{"](.+?)[}"],?\s*\n', c, re.S)
        v = re.search(r'(?:booktitle|journal)\s*=\s*[{"](.+?)[}"]', c, re.S)
        s = re.search(r'series\s*=\s*[{"](.+?)[}"]', c, re.S)
        if d:
            out[k.strip()] = (d.group(1).strip(),
                              re.sub(r'[{}]', '', t.group(1)) if t else '',
                              re.sub(r'[{}]', '', v.group(1)) if v else '',
                              re.sub(r'[{}]', '', s.group(1)) if s else '')
    return out


def tem_rede():
    r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                        '--max-time', '8', 'https://api.crossref.org/works/10.1145/1198302.1198305'],
                       capture_output=True, text=True)
    return r.stdout.strip() == '200'


def toks(s):
    s = re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower())
    stop = {'proceedings', 'proc', 'of', 'the', 'ieee', 'cvf', 'acm', 'international',
            'conference', 'on', 'in', 'workshop', 'workshops', 'annual', 'joint', 'th',
            'st', 'nd', 'rd', 'and', 'lecture', 'notes', 'computer', 'science', 'series'}
    return {w for w in s.split() if w not in stop and len(w) > 1}


def iniciais(nome):
    """As iniciais das palavras de conteudo: «Transactions on Circuits and Systems for
    Video Technology» -> «TCSVT»."""
    stop = {'of', 'the', 'on', 'in', 'and', 'for', 'a', 'an', 'ieee', 'acm', 'proceedings'}
    ws = [w for w in re.findall(r'[A-Za-z]+', nome) if w.lower() not in stop]
    return ''.join(w[0].upper() for w in ws)


def titulo_confere(reg, meu):
    """O registro e a entrada falam do mesmo artigo? Os dois erros de um digito caiam
    noutro artigo do MESMO proceedings, entao so o titulo separa."""
    a, b = norm(reg), norm(meu)
    return not (a and b) or a.startswith(b[:32]) or b.startswith(a[:32])


def local_confere(meu, reg, ev, serie=''):
    """⚠️ Comparar PALAVRAS nao separa: «Proc. IEEE BMSB» e «...Broadband Multimedia...»
    compartilham «multimedia», e o local certo era ICMEW. O que distingue e a SIGLA.

    ⚠️ Mas a sigla nem sempre aparece literal. Tres casos reais deste .bib:
      «TCSVT»  sao as iniciais de «Transactions on Circuits and Systems for Video Technology»;
      «CVPR»   num registro «...Conference on Computer Vision and Pattern Recognition
               Workshops» so aparece DENTRO das iniciais (CCVPRW), nao como palavra;
      «ECCV»   nao aparece em lugar nenhum: o registro traz a SERIE, «Lecture Notes in
               Computer Science», e o evento vem vazio.
    Entao: sigla literal, OU sigla dentro das iniciais, OU a serie que o .bib declara
    batendo com o registro.

    ⚠️ LIMITE DECLARADO: no caso da serie o local so se confere AO NIVEL DA SERIE — duas
    conferencias diferentes da LNCS passam igual. Quem separa a errada ali e a conferencia
    de TITULO, que roda em cima do mesmo registro.
    """
    siglas = [s for s in re.findall(r'\b[A-Z]{2,}\b', meu)
              if s not in ('IEEE', 'ACM', 'CVF', 'LNCS')]
    alvo = reg + ' ' + ev
    # a serie pode vir por sigla («LNCS») ou por extenso; nos dois casos ela se reduz
    # a mesma assinatura antes de comparar
    def sig(x):
        x = x.strip()
        return x.upper() if re.fullmatch(r'[A-Za-z]{2,8}', x) else iniciais(x)
    if serie and reg and sig(serie) == sig(reg):
        return True
    if siglas:
        for s in siglas:
            if re.search(r'\b' + re.escape(s) + r'\b', alvo, re.I):
                return True
            if s in iniciais(reg) or s in iniciais(ev):
                return True
        return False
    meu_t, alvo_t = toks(meu), toks(reg) | toks(ev)
    return not meu_t or not alvo_t or bool(meu_t & alvo_t)


CACHE = AQUI / '.cache_crossref.json'


def _registro(doi):
    """Le da Crossref com cache em disco: sem isso a suite bate 74 vezes na rede."""
    try:
        c = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    except Exception:
        c = {}
    if doi in c:
        return c[doi]
    r = subprocess.run(['curl', '-sL', '--max-time', '12',
                        'https://api.crossref.org/works/' + doi], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)['message']
        v = {'title': (d.get('title') or [''])[0],
             'container': (d.get('container-title') or [''])[0],
             'event': (d.get('event') or {}).get('name') or ''}
    except Exception:
        v = None
    c[doi] = v
    CACHE.write_text(json.dumps(c, ensure_ascii=False))
    return v


def confere():
    ruins, n = [], 0
    for k, (doi, titulo, local, serie) in sorted(entradas().items()):
        if doi.startswith('10.48550'):      # arXiv nao esta na Crossref
            continue
        if k in ACEITOS:
            continue
        n += 1
        d = _registro(doi)
        if d is None:
            ruins.append('%s: o DOI %s nao resolve' % (k, doi))
            continue
        reg = d['title']
        if not titulo_confere(reg, titulo):
            ruins.append('%s: o DOI aponta para %r' % (k, reg[:56]))
        # e o local de publicacao, que errou uma vez sem que nada acusasse
        cont, ev = d['container'], d['event']
        if local and cont and not local_confere(local, cont, ev, serie) \
                and k not in LOCAL_ACEITO:
            ruins.append('%s: o .bib diz %r, o registro diz %r' % (k, local[:30], cont[:44]))
    return not ruins, ruins, n


def autoteste():
    """⚠️ As DUAS pernas. Uma guarda que so aprova o mundo certo nao separa nada: ela
    precisa REPROVAR o defeito reintroduzido. Roda offline, em cima do cache."""
    global entradas
    casos_bons = [
        # (bib, container do registro, evento, serie)   — todos reais deste .bib
        ('Proc. IEEE CVPR Workshops',
         '2014 IEEE Conference on Computer Vision and Pattern Recognition Workshops',
         '... Workshops (CVPRW)', ''),
        ('IEEE TCSVT', 'IEEE Transactions on Circuits and Systems for Video Technology', '', ''),
        ('Proc. ECCV', 'Lecture Notes in Computer Science', '', 'LNCS'),
    ]
    casos_maus = [
        # ⛔ o defeito real de 08/09: o .bib dizia BMSB, e o local era ICMEW
        ('Proc. IEEE BMSB',
         '2023 IEEE International Conference on Multimedia and Expo Workshops (ICMEW)', '', ''),
        # ⛔ e um rival de mesma familia: ICME nao e CVPR
        ('Proc. IEEE ICME',
         '2017 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)', '', ''),
        # ⛔ serie declarada que NAO e a do registro
        ('Proc. ECCV', 'IEEE Transactions on Image Processing', '', 'LNCS'),
    ]
    falhas = []
    for c in casos_bons:
        if not local_confere(*c):
            falhas.append('reprovou um local legitimo: %r x %r' % (c[0], c[1][:40]))
    for c in casos_maus:
        if local_confere(*c):
            falhas.append('aprovou um local errado: %r x %r' % (c[0], c[1][:40]))
    # ⛔ o defeito de UM DIGITO: o DOI resolve, do ano e da conferencia certos, e aponta
    # para outro artigo. Aqui com um par que ja esta no cache, para rodar sem rede.
    if titulo_confere('Deep Residual Learning for Image Recognition',
                      'Q-Instruct: Improving Low-Level Visual Abilities'):
        falhas.append('aprovou um DOI que aponta para outro artigo')
    if not titulo_confere('Creating Summaries from User Videos', 'Creating Summaries from User Videos'):
        falhas.append('reprovou um DOI correto')
    # e a perna de ponta a ponta: planta a entrada errada e confere() tem de acusar
    orig = entradas
    entradas = lambda: {'plantado': ('10.1109/CVPR.2016.90',
                                     'Q-Instruct: Improving Low-Level Visual Abilities',
                                     'Proc. IEEE CVPR', '')}
    try:
        ok, ruins, _ = confere()
    finally:
        entradas = orig
    if ok or not any('plantado' in x for x in ruins):
        falhas.append('confere() nao acusou a entrada plantada')
    for f in falhas:
        print('    ⛔ autoteste: %s' % f)
    return not falhas


if __name__ == '__main__':
    if not autoteste():
        print('  ⛔ REPROVA (a propria guarda nao separa)')
        sys.exit(1)
    if not tem_rede():
        print('  ⏳ sem rede: a conferencia de DOI nao rodou (nao aprova nem reprova)')
        sys.exit(3)
    ok, ruins, n = confere()
    print('  %d DOIs conferidos contra a Crossref (%d aceitos com motivo declarado)'
          % (n, len(ACEITOS)))
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
