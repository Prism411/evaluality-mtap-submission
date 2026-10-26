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
PAPERS = Path('/home/user/workspace/library/papers')
CACHE = Path('/tmp/claude-1000/-home-author-Desktop-estudos-workspace-notes/'
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
        # ⛔ 21/09: conferir SO o primeiro autor deixou passar TRES COAUTORES FABRICADOS no
        # `qaroush2025diversity` — o .bib trazia «Daoud, Alsafadi, Kanaan» e o artigo
        # publicado (ESWA 292, 128631) traz «Jubran, Olayyan, Qutait». O primeiro autor e o
        # ano estavam certos, entao a guarda dizia ✅. Um parecer externo pegou o que ela
        # nao pegava. ⭐ Agora confere TODOS os sobrenomes.
        todos_sobr = []
        if bruto:
            for autor in re.split(r'\s+and\s+', bruto):
                autor = autor.strip().strip('{}').strip()
                if not autor:
                    continue
                # «Sobrenome, Nome» ou «Nome Sobrenome»
                sob = autor.split(',')[0].strip() if ',' in autor else autor.split()[-1]
                sob = sob.strip('{}. ').strip()
                if sob:
                    todos_sobr.append(sob)
        out[k.strip()] = {
            'sobrenome': (re.split(r',| and ', bruto)[0].strip().split()[-1]
                          if bruto else None),
            'sobrenomes': todos_sobr,
            'ano': y.group(1) if y else None,
            'doi': (lambda d: d.group(1) if d else None)(re.search(r'doi\s*=\s*[{"]([^}"]+)', corpo, re.I)),
            'titulo': re.sub(r'[^a-z0-9 ]', '', t.group(1).lower()) if t else None}
    return out


def citadas(aux=None):
    if aux is not None:
        fontes = [aux]
    else:
        fontes = [f for f in (AQUI / 'main.aux', AQUI / 'supplementary.aux') if f.exists()]
    out = set()
    for f in fontes:
        a = f.read_text(errors='replace')
        out |= {c.strip() for m in re.findall(r'\\citation\{([^}]*)\}', a)
                for c in m.split(',') if c.strip()}
    return out


def _texto(pdf):
    CACHE.mkdir(parents=True, exist_ok=True)
    alvo = CACHE / (pdf.stem + '.txt')
    if not alvo.exists():
        # ⚠️ so as 2 primeiras paginas reprovava 7 de 18 entradas CORRETAS: muitos artigos
        # nao imprimem o ano na abertura. Le o documento inteiro.
        subprocess.run(['pdftotext', str(pdf), str(alvo)], check=False, capture_output=True)
    return re.sub(r'\s+', ' ', alvo.read_text(errors='ignore')).lower() \
        if alvo.exists() else ''


def _primeira_pagina(pdf):
    """So a folha de rosto. ⛔ O casamento por titulo NAO pode ler o documento inteiro."""
    CACHE.mkdir(parents=True, exist_ok=True)
    alvo = CACHE / (pdf.stem + '.p1.txt')
    if not alvo.exists():
        subprocess.run(['pdftotext', '-f', '1', '-l', '1', str(pdf), str(alvo)],
                       check=False, capture_output=True)
    return re.sub(r'\s+', ' ', alvo.read_text(errors='ignore')).lower() \
        if alvo.exists() else ''


def acha_pdf(chave, meta, todos=None):
    """Pelo citekey; se falhar, pelo TITULO — foi assim que o Gygli aparecera perdido.

    ⛔ CONSERTADO em 21/09. O casamento por titulo procurava no texto INTEIRO, e o titulo
    de um trabalho aparece na LISTA DE REFERENCIAS de outros. O `robitza2021siti`, que NAO
    esta no acervo, casou com `eswa2026attention_dyngnn.pdf` e foi contado como conferido:
    o sobrenome e o ano tambem estavam la, na mesma entrada da bibliografia alheia.
    ⭐ O titulo agora so casa na PRIMEIRA PAGINA, onde so o proprio artigo o imprime.
    """
    p = PAPERS / f'{chave}.pdf'
    if p.exists():
        return p
    if not meta.get('titulo'):
        return None
    alvo = ' '.join(meta['titulo'].split()[:6])
    for q in (todos if todos is not None else sorted(PAPERS.glob('*.pdf'))):
        if alvo and alvo in _primeira_pagina(q):
            return q
    return None


# ⚠️ Tres PDFs do acervo sao PREPRINT/camera-ready SEM o ano impresso em lugar nenhum.
# Conferi os tres a mao contra o local de publicacao e estao CERTOS; ficam declarados aqui
# em vez de a checagem ser afrouxada para todos.
SEM_ANO_NO_PDF = {
    # ⚠️ preprint arXiv sem ano impresso; autores e titulo conferem na primeira pagina
    # («Beyond the Frame: Single and multiple video summarization method with
    # user-defined length», Kalkhorani, Zhang, Song, Zhu).
    'kalkhorani2024beyond_frame': 'preprint arXiv; PDF sem ano impresso',
    # ⚠️ camera-ready do ICME com o cabecalho em fonte codificada: o `pdftotext` devolve
    # «*&&&*OUFSOBUJPOBM$POGFSFODF…» e nenhum ano legivel. Titulo e autores conferem.
    'lei2019framerank': 'ICME 2019; cabecalho do PDF em codificacao ilegivel',
    'li2010videommr': 'WIAMIS 2010, Li e Merialdo (Eurecom); PDF sem ano impresso',
    'mittal2013niqe': 'IEEE SPL 20(3), marco de 2013; PDF e preprint sem ano',
    # ⚠️ o .bib cita a publicacao (ICML 2024, PMLR 235) e o PDF aberto e o preprint de
    # dez/2023. O ano PUBLICADO esta certo; e o preprint que e anterior.
    'wu2024qalign': 'ICML 2024; o arXiv aberto e o preprint de 2023',
    # ⚠️ os dois PDFs abertos sao versao de autor, sem o ano impresso na primeira
    # pagina; o .bib cita o local de publicacao, que confere no cabecalho.
    'ghadiyaram2016clive': 'IEEE TIP 25(1), 2016; PDF de autor sem ano impresso',
    'zhang2020dbcnn': 'IEEE TCSVT 30(1), 2020; o arXiv aberto e o preprint de 2019',
    # ⚠️ mesmo padrao: preprint no arXiv anterior a publicacao. O local de publicacao
    # foi conferido a mao no cabecalho de cada um.
    'agnolucci2024arniqa': 'WACV 2024; o arXiv aberto e de nov/2023',
    'chen2024topiq': 'IEEE TIP 2024; o arXiv aberto e de ago/2023',
    'golestaneh2022tres': 'WACV 2022; o arXiv aberto nao imprime o ano',
    'panda2017collaborative': 'CVPR 2017, Panda e Roy-Chowdhury; PDF sem ano',
}


def _normaliza(s):
    """Acento fora e minuscula: o PDF imprime «Süsstrunk», o .bib escreve «S{\\"u}sstrunk».

    ⚠️ Tira TAMBEM os marcadores de acento que nao sao letra (`\\"`, `\\'`, `\\`` , `\\^`,
    `\\~`): deixar o `"` para tras transformava «Süsstrunk» em «s"usstrunk» e produzia
    falso positivo. Os acentos ja escritos em UTF-8 caem pela decomposicao NFKD.
    """
    import unicodedata
    s = re.sub(r'\\[a-zA-Z]+', '', s)          # \c, \ss, \relax...
    s = re.sub(r'[{}\\"\'`^~]', '', s)         # chaves, barra e marcadores de acento
    s = unicodedata.normalize('NFKD', s)
    return ''.join(ch for ch in s if not unicodedata.combining(ch)).lower()


# ⚠️ `and others` e a forma BibTeX de «et al.»: nao e sobrenome e nao se procura no PDF.
NAO_E_SOBRENOME = {'others'}


# ⚠️ PDFs em que a lista de autores nao sai legivel do `pdftotext` (coluna, figura ou
# codificacao). Cada um foi conferido A MAO contra a pagina do editor e esta CERTO; fica
# declarado aqui em vez de a checagem ser afrouxada para todos.
COAUTOR_NAO_IMPRESSO = {}


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
        # ⭐ TODOS os coautores, e nao so o primeiro: foi por aqui que passaram os tres
        # nomes fabricados do `qaroush2025diversity`.
        ausentes = [s for s in m.get('sobrenomes', [])[1:]
                    if _normaliza(s) not in NAO_E_SOBRENOME
                    and _normaliza(s) not in _normaliza(t)
                    and c not in COAUTOR_NAO_IMPRESSO]
        if ausentes:
            falhas.append('coautor(es) ausente(s) no PDF: ' + ', '.join(repr(a) for a in ausentes))
        tem_doi = bool(m.get('doi'))
        if m['ano'] and m['ano'] not in t and c not in SEM_ANO_NO_PDF and not tem_doi:
            falhas.append(f"ano {m['ano']} ausente e a entrada nao tem DOI que o confirme")
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

    # ⭐ CONTROLE POSITIVO DO COAUTOR (21/09): reintroduz o defeito de verdade e exige que
    # a guarda o reprove. Sem esta perna, «✅ nenhuma divergencia» so diria que o primeiro
    # autor confere — que foi exatamente como os tres nomes fabricados sobreviveram.
    q = 'qaroush2025diversity'
    assert q in m, 'a entrada do controle sumiu'
    reais = m[q]['sobrenomes']
    assert len(reais) >= 2, '⛔ o controle precisa de uma entrada com coautor'
    tq = _texto(acha_pdf(q, m[q]))
    assert all(_normaliza(s) in _normaliza(tq) for s in reais), \
        '⛔ os coautores REAIS deveriam aparecer no PDF: %s' % reais
    for falso in ('Daoud', 'Alsafadi', 'Kanaan'):   # os tres que estavam no .bib ate 21/09
        assert _normaliza(falso) not in _normaliza(tq), \
            '⛔ NAO DISCRIMINA: o coautor fabricado %r foi achado no PDF' % falso
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
    # ⭐ 21/09 (parecer, B01): «conferidas» sozinho nao diz o que NAO foi verificado, e o
    # parecer pede que o inventario marque isso. Tres niveis, e nenhum deles e ✅ implicito.
    import re as _re
    _bib = (AQUI / 'references.bib').read_text(encoding='utf-8')
    _bib = '\n'.join(l for l in _bib.split('\n') if not l.lstrip().startswith('%'))
    _com_doi = {k for k, c in _re.findall(r'@\w+\{([^,]+),(.*?)\n\}', _bib, _re.S)
                if _re.search(r'\bdoi\s*=', c)}
    _so_doi = sorted(set(sem) & _com_doi)
    _nada = sorted(set(sem) - _com_doi)
    json.dump({'_o_que_e': __doc__.strip(), 'citadas': n, 'conferidas': n_ok,
               'divergem': [{'chave': c, 'motivo': m} for c, m in ruins],
               'sem_pdf_no_acervo': sem,
               '_cobertura': {
                   '_como_ler': 'tres niveis, do mais forte ao mais fraco. ⛔ «conferidas» '
                                'NAO quer dizer que a obra foi lida: sao autores e ano '
                                'batidos contra o texto do PDF.',
                   'autoria_e_ano_contra_o_pdf': n_ok,
                   'so_doi_contra_a_crossref': len(_so_doi),
                   'sem_nenhuma_verificacao': len(_nada),
                   'quais_sem_nenhuma_verificacao': _nada}},
              open(AQUI / 'bibliografia_conferida.json', 'w'), indent=1, ensure_ascii=False)
    print('  cobertura: %d contra o PDF, %d so por DOI, %d sem verificacao alguma'
          % (n_ok, len(_so_doi), len(_nada)))
    sys.exit(0 if ok else 1)
