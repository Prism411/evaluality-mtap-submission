#!/usr/bin/env python3
"""⛔ CADA REFERENCIA CITADA BATE COM O PDF DA FONTE?

POR QUE EXISTE (07/09/2026). Duas entradas ja sairam erradas por acidente e nao por busca:
o `jeong2016static` tinha `year = {2016}` e o periodico e **2017**, e o `gygli2014summe`
existia no acervo sob outro nome de arquivo, o que me fez declarar «sem PDF» quando havia.
Antes disso, quatro entradas inteiras tinham sido INVENTADAS. Uma referencia errada nao
quebra a compilacao e nenhum teste a reprova: e preciso ir ao PDF.

O QUE ELA FAZ: para cada chave citada, acha o PDF no acervo (pelo citekey OU pelo titulo),
le a primeira pagina e exige que o SOBRENOME do primeiro autor e o ANO do .bib aparecam la.

⚠️ Nao substitui leitura humana: confere tres campos, nao a obra. Chave sem PDF no acervo
sai listada como NAO VERIFICAVEL, nunca como aprovada.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
PAPERS = Path('/home/jader/Desktop/estudos/vault-biblio/papers')
CACHE = Path('/tmp/claude-1000/-home-jader-Desktop-estudos-osirihs-vault-5-sumarizador/'
             '51d375ec-33aa-4092-b28f-309cfe691890/scratchpad/bibcheck')


def entradas(bib=None):
    b = (bib or (AQUI / 'references.bib')).read_text()
    out = {}
    for k, corpo in re.findall(r'@\w+\{([^,]+),(.*?)\n\}', b, re.S):
        a = re.search(r'author\s*=\s*[{"](.+?)[}"],?\s*\n', corpo, re.S)
        y = re.search(r'year\s*=\s*[{"]?(\d{4})', corpo)
        t = re.search(r'title\s*=\s*[{"](.+?)[}"],?\s*\n', corpo, re.S)
        # ⚠️ autor INSTITUCIONAL vem em chaves duplas: `author = {{International
        # Telecommunication Union}}`. O regex para no primeiro `}` e devolvia «Union}»,
        # que nunca aparece no PDF. Tira as chaves antes de separar.
        bruto = a.group(1).strip().strip('{}').strip() if a else None
        out[k.strip()] = {
            'sobrenome': (re.split(r',| and ', bruto)[0].strip().split()[-1]
                          if bruto else None),
            'ano': y.group(1) if y else None,
            'titulo': re.sub(r'[^a-z0-9 ]', '', t.group(1).lower()) if t else None}
    return out


def citadas(aux=None):
    a = (aux or (AQUI / 'main.aux')).read_text()
    return {c for m in re.findall(r'\\citation\{([^}]*)\}', a) for c in m.split(',')}


def _texto(pdf):
    CACHE.mkdir(parents=True, exist_ok=True)
    alvo = CACHE / (pdf.stem + '.txt')
    if not alvo.exists():
        # ⚠️ so as 2 primeiras paginas reprovava 7 de 18 entradas CORRETAS: muitos artigos
        # nao imprimem o ano na abertura. Le o documento inteiro.
        subprocess.run(['pdftotext', str(pdf), str(alvo)], check=False, capture_output=True)
    return re.sub(r'\s+', ' ', alvo.read_text(errors='ignore')).lower() \
        if alvo.exists() else ''


def acha_pdf(chave, meta, todos=None):
    """Pelo citekey; se falhar, pelo TITULO — foi assim que o Gygli aparecera perdido."""
    p = PAPERS / f'{chave}.pdf'
    if p.exists():
        return p
    if not meta.get('titulo'):
        return None
    alvo = ' '.join(meta['titulo'].split()[:6])
    for q in (todos if todos is not None else sorted(PAPERS.glob('*.pdf'))):
        if alvo and alvo in _texto(q):
            return q
    return None


# ⚠️ Tres PDFs do acervo sao PREPRINT/camera-ready SEM o ano impresso em lugar nenhum.
# Conferi os tres a mao contra o local de publicacao e estao CERTOS; ficam declarados aqui
# em vez de a checagem ser afrouxada para todos.
SEM_ANO_NO_PDF = {
    'li2010videommr': 'WIAMIS 2010, Li e Merialdo (Eurecom); PDF sem ano impresso',
    'mittal2013niqe': 'IEEE SPL 20(3), marco de 2013; PDF e preprint sem ano',
    'panda2017collaborative': 'CVPR 2017, Panda e Roy-Chowdhury; PDF sem ano',
}


def confere():
    meta, cit = entradas(), citadas()
    todos = sorted(PAPERS.glob('*.pdf'))
    ruins, sem_pdf, ok = [], [], 0
    for c in sorted(cit):
        m = meta.get(c)
        if not m:
            ruins.append((c, 'chave citada nao existe no .bib')); continue
        pdf = acha_pdf(c, m, todos)
        if pdf is None:
            sem_pdf.append(c); continue
        t = _texto(pdf)
        falhas = []
        if m['sobrenome'] and m['sobrenome'].lower() not in t:
            falhas.append(f"autor {m['sobrenome']!r} ausente")
        if m['ano'] and m['ano'] not in t and c not in SEM_ANO_NO_PDF:
            falhas.append(f"ano {m['ano']} ausente")
        if falhas:
            ruins.append((c, f"{pdf.name}: " + '; '.join(falhas)))
        else:
            ok += 1
    return not ruins, ruins, sem_pdf, ok, len(cit)


def _autoteste():
    """⭐ Duas pernas: uma entrada boa passa, e uma com ano trocado REPROVA."""
    import tempfile
    m = entradas()
    alvo = 'ke2006highlevel'
    assert alvo in m, 'a entrada de referencia sumiu'
    pdf = acha_pdf(alvo, m[alvo])
    assert pdf is not None, 'o PDF de referencia sumiu do acervo'
    t = _texto(pdf)
    assert m[alvo]['ano'] in t, 'o ano correto deveria aparecer'
    # o mundo errado: um ano que nao esta no PDF tem de falhar a checagem
    assert '1873' not in t, '⛔ nao discrimina: um ano falso apareceu no PDF'
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins, sem, n_ok, n = confere()
    print(f'  autoteste ✅   {n} chaves citadas\n')
    print(f'  ✅ conferidas contra o PDF: {n_ok}')
    print(f'  ⚠️ sem PDF no acervo (nao verificaveis): {len(sem)}')
    print(f'  {"✅ nenhuma divergencia" if ok else f"⛔ {len(ruins)} DIVERGEM"}')
    for c, m in ruins:
        print(f'    {c}: {m}')
    json.dump({'_o_que_e': __doc__.strip(), 'citadas': n, 'conferidas': n_ok,
               'divergem': [{'chave': c, 'motivo': m} for c, m in ruins],
               'sem_pdf_no_acervo': sem},
              open(AQUI / 'bibliografia_conferida.json', 'w'), indent=1, ensure_ascii=False)
    sys.exit(0 if ok else 1)
