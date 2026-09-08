#!/usr/bin/env python3
"""⛔ CADA DOI DO .BIB APONTA PARA O ARTIGO QUE A ENTRADA DIZ SER?

POR QUE EXISTE (08/09/2026). Um DOI errado passa por tudo: o LaTeX compila, a bibliografia
imprime, e a citacao parece perfeita. So quem CLICA descobre. Encontrei quatro:

  ⛔ `wu2024qinstruct`  .02412 apontava para «Navigating Beyond Dropout»
  ⛔ `ye2024mplugowl2`  .01238 apontava para «Pixel Aligned Language Models»
  ⛔ `moraes2022subjectivity`  DOI da WebMedia dava 404; o certo e o da ACM
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
        if d:
            out[k.strip()] = (d.group(1).strip(),
                              re.sub(r'[{}]', '', t.group(1)) if t else '')
    return out


def tem_rede():
    r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                        '--max-time', '8', 'https://api.crossref.org/works/10.1145/1198302.1198305'],
                       capture_output=True, text=True)
    return r.stdout.strip() == '200'


def confere():
    ruins, n = [], 0
    for k, (doi, titulo) in sorted(entradas().items()):
        if doi.startswith('10.48550'):      # arXiv nao esta na Crossref
            continue
        if k in ACEITOS:
            continue
        n += 1
        r = subprocess.run(['curl', '-sL', '--max-time', '12',
                            'https://api.crossref.org/works/' + doi],
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)['message']
        except Exception:
            ruins.append('%s: o DOI %s nao resolve' % (k, doi))
            continue
        reg = (d.get('title') or [''])[0]
        a, b = norm(reg), norm(titulo)
        if a and b and not (a.startswith(b[:32]) or b.startswith(a[:32])):
            ruins.append('%s: o DOI aponta para %r' % (k, reg[:56]))
    return not ruins, ruins, n


if __name__ == '__main__':
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
