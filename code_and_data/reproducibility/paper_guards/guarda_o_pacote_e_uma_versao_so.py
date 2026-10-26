#!/usr/bin/env python3
r"""⛔ O FONTE, OS PDFs E O ARQUIVO DE REPRODUCAO SAO A MESMA VERSAO?

POR QUE EXISTE (15/09/2026). O parecer listou como ultima entrega «conferir que o fonte, os
PDFs e o arquivo de reproducao correspondem a mesma versao». Havia guardas para cada peca
isolada — o repo tem o gerador atual, um clone compila, o clone reproduz seis numeros — mas
**nenhuma provava que as tres pecas sao a MESMA versao ao mesmo tempo**.

🔴 E ja houve o caso: a `guarda_repo_compila_do_zero` aprovava «um clone limpo compila os
dois» com **34 paginas** enquanto o pacote local dava **31**, porque `git clone` copia o
ultimo commit e nao a arvore sincronizada. Cada peca estava certa sozinha.

⭐ Esta guarda casa as tres:
  1. todo `.tex` e `.py` do pacote e byte-identico ao publicado;
  2. **recompilar o fonte publicado reproduz o PDF publicado** — mesma contagem de paginas e
     mesmo texto extraido (o byte do PDF muda pelo carimbo de data, o texto nao);
  3. todo artefato que os geradores leem esta declarado na lista publicada.
"""
import hashlib, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

A = Path(__file__).parent
REPO = Path('/data/projects/submission-package')
DOCS = [('paper', 'main'), ('supplement', 'supplementary')]
FONTES = [('sec_*.tex', 'paper'), ('main.tex', 'paper'),
          ('graphical_abstract.tex', 'paper'), ('supplementary.tex', 'supplement'),
          ('gera_*.py', 'reproducibility/paper_generators'),
          ('guarda_*.py', 'reproducibility/paper_guards'),
          # ⛔ ACRESCENTADOS em 21/09. Os dois foram levados A MAO na sincronia anterior
          # porque nao casam padrao nenhum acima, e os dois quebrariam o pacote em
          # silencio: `macros_jusante.tex` e `\input` do `main.tex` e sem ele o pacote
          # NAO COMPILA; `cnn_bovw_scorer.py` nao e `gera_*` nem `guarda_*` e carrega o
          # recuo de NaN da MobileNet-V3, sem o qual a ablacao nao roda.
          # 📌 Uma guarda de sincronia so cobre o que o padrao dela alcanca.
          ('macros_jusante.tex', 'paper'),
          ('cnn_bovw_scorer.py', 'reproducibility'),
          # ⛔ 21/09, o terceiro: o ORQUESTRADOR da suite tambem nao casava padrao nenhum,
          # entao a guarda de sincronia nao cobria o arquivo que RODA a guarda de
          # sincronia. Estava publicado e divergente, sem nada acusar.
          ('verifica_tudo.py', 'reproducibility'),
          ('sincroniza_ponteiros.py', 'reproducibility'),
          ('caminho_dos_dados.py', 'reproducibility'),
          # ⭐ 22/09: o `checklist_48.py` foi publicado no pacote e ficaria fora do mapa
          # pelo mesmo motivo dos tres acima — nao casa `gera_*` nem `guarda_*`. Entra
          # aqui na hora de publicar, e nao depois de alguem notar que divergiu.
          ('checklist_48.py', 'reproducibility')]
# o que as DUAS pastas precisam ter, e identico
COMPARTILHADOS = ['tab_*.tex', 'fig_*.tex', 'regras_publicadas.tex', 'references.bib']
for _p in COMPARTILHADOS:
    FONTES += [(_p, 'paper'), (_p, 'supplement')]


def texto_do_pdf(p):
    r = subprocess.run(['pdftotext', str(p), '-'], capture_output=True, text=True)
    return re.sub(r'\s+', ' ', r.stdout).strip()


def paginas(p):
    r = subprocess.run(['pdfinfo', str(p)], capture_output=True, text=True).stdout
    for l in r.split('\n'):
        if l.lower().startswith('pages'):
            return int(l.split()[-1])
    return None


def fontes_divergentes():
    ruins = []
    for padrao, sub in FONTES:
        for q in sorted(A.glob(padrao)):
            alvo = REPO / sub / q.name
            if not alvo.exists():
                ruins.append('%s nao esta publicado em %s/' % (q.name, sub))
            elif alvo.read_bytes() != q.read_bytes():
                ruins.append('%s difere do publicado em %s/' % (q.name, sub))
    return ruins


def pdf_vem_do_fonte_publicado():
    """Recompila o FONTE PUBLICADO num diretorio novo e compara com o PDF PUBLICADO."""
    ruins = []
    with tempfile.TemporaryDirectory() as td:
        raiz = Path(td)
        for pasta, doc in DOCS:
            d = raiz / pasta
            shutil.copytree(REPO / pasta, d)
            for cmd in (['pdflatex', '-interaction=nonstopmode', doc + '.tex'],
                        ['bibtex', doc],
                        ['pdflatex', '-interaction=nonstopmode', doc + '.tex'],
                        ['pdflatex', '-interaction=nonstopmode', doc + '.tex']):
                subprocess.run(cmd, cwd=d, capture_output=True)
            novo, publicado = d / (doc + '.pdf'), REPO / pasta / (doc + '.pdf')
            if not novo.exists():
                ruins.append('%s nao compilou a partir do fonte publicado' % doc)
                continue
            pn, pp = paginas(novo), paginas(publicado)
            if pn != pp:
                ruins.append('%s: o fonte publicado da %s paginas e o PDF publicado tem %s'
                             % (doc, pn, pp))
            elif texto_do_pdf(novo) != texto_do_pdf(publicado):
                ruins.append('%s: mesma contagem de paginas, mas o TEXTO difere — o PDF '
                             'publicado nao veio deste fonte' % doc)
    return ruins


def artefatos_declarados():
    lista = A / 'artefatos_que_o_artigo_le.json'
    if not lista.exists():
        return ['a lista de artefatos nao existe: nao se decide']
    d = json.loads(lista.read_text(encoding='utf-8'))
    faltam = d.get('faltam_no_repositorio') or []
    ausentes = [x for x in faltam if not (REPO / x).exists()]
    return (['%d artefato(s) que os geradores leem nao estao no repositorio: %s'
             % (len(ausentes), ausentes[:3])] if ausentes else [])


def confere():
    if not REPO.exists():
        return ['o repositorio nao esta neste disco']
    return fontes_divergentes() + artefatos_declarados() + pdf_vem_do_fonte_publicado()


def main():
    r = confere()
    for x in r:
        print('  ⛔ %s' % x)
    if not r:
        print('  ✅ fonte, PDFs e artefatos sao a mesma versao: o fonte publicado recompila '
              'os PDFs publicados')
    return 1 if r else 0


def autoteste():
    mal = 0
    n = len(fontes_divergentes()) + len(artefatos_declarados())
    print(f"  {'✅' if n == 0 else '⛔'} fonte e artefatos: {n} divergencia(s), esperado 0")
    mal += n != 0
    # ⛔ a perna que separa: um fonte alterado sem republicar o PDF tem de REPROVAR
    alvo = REPO / 'paper' / 'sec_intro.tex'
    if alvo.exists():
        orig = alvo.read_bytes()
        try:
            alvo.write_bytes(orig + b'\n\n\\noindent Sentenca plantada pelo autoteste.\n')
            n = len(pdf_vem_do_fonte_publicado())
            print(f"  {'✅' if n >= 1 else '⛔'} fonte alterado sem republicar: {n}, esperado >=1")
            mal += n < 1
        finally:
            alvo.write_bytes(orig)
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
