#!/usr/bin/env python3
"""RODA A SUITE INTEIRA: geradores, build e as sete guardas, nesta ordem.

POR QUE EXISTE (08/09/2026). As guardas so valem se rodarem, e rodar sete comandos a mao
depois de cada edicao nao escala: em 08/09 eu editei a tabela e so descobri no fim que uma
guarda estava lendo um arquivo que tinha saido do artigo.

ORDEM QUE IMPORTA:
  1. os geradores reescrevem os .tex a partir do JSON medido;
  2. o suplementar compila PRIMEIRO, porque o `sincroniza_ponteiros` le o .aux dele;
  3. os ponteiros do corpo sao sincronizados;
  4. o corpo compila;
  5. as guardas rodam sobre o que ficou em disco.

Saida 0 so se TODAS aprovarem.
"""
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
PY = '/data/projects/pipeline/.venv/bin/python'

GERADORES = sorted(p.name for p in AQUI.glob('gera_*.py'))
GUARDAS = sorted(p.name for p in AQUI.glob('guarda_*.py'))


def roda(cmd, **kw):
    return subprocess.run(cmd, cwd=AQUI, capture_output=True, text=True, **kw)


def latex(doc):
    roda(['pdflatex', '-interaction=nonstopmode', doc + '.tex'])
    roda(['bibtex', doc])
    for _ in range(2):
        roda(['pdflatex', '-interaction=nonstopmode', doc + '.tex'])


def paginas(pdf):
    out = roda(['pdfinfo', pdf]).stdout
    for l in out.split('\n'):
        if l.lower().startswith('pages'):
            return int(l.split()[-1])
    return -1


def main():
    print('\n[1/5] geradores')
    for g in GERADORES:
        r = roda([PY, g])
        marca = '✅' if r.returncode == 0 else '⛔'
        print('   %s %s' % (marca, g))
        if r.returncode:
            print(r.stderr.strip()[:400])
            return 2

    print('\n[2/5] suplementar')
    latex('supplementary')
    print('\n[3/5] ponteiros do corpo para o suplementar')
    r = roda([PY, 'sincroniza_ponteiros.py'])
    print('   ' + [l for l in r.stdout.strip().split('\n') if '✅' in l or '⛔' in l][-1])

    print('\n[4/5] corpo')
    latex('main')

    # ⛔ o abstract grafico e um entregavel SEPARADO e nao entra em nenhum \input, entao
    # envelhecia em silencio: em 08/09 o .pdf era de 17:19 e o .tex de 00:46, e o PDF que
    # o revisor veria ainda tinha o travessao ja corrigido na fonte.
    roda(['pdflatex', '-interaction=nonstopmode', 'graphical_abstract.tex'])
    # ⭐ 27/09: a carta de apresentacao e um entregavel separado pelo MESMO
    # motivo, e cita numeros por macro. Um .tex que nada compila apodrece:
    # foi exatamente o que aconteceu com o resumo grafico em 08/09.
    roda(['pdflatex', '-interaction=nonstopmode', 'cover_letter.tex'])

    print('\n[5/5] guardas')
    falhou, pendentes = [], []
    for g in GUARDAS:
        if g == 'guarda_' or not g.startswith('guarda_'):
            continue
        r = roda([PY, g])
        marca = {0: '✅', 3: '⏳'}.get(r.returncode, '⛔')
        print('   %s %s' % (marca, g))
        if r.returncode == 3:
            pendentes.append(g)
            print('      ' + (r.stdout + r.stderr).strip().split('\n')[-2])
        elif r.returncode:
            falhou.append(g)
            print('      ' + '\n      '.join(
                (r.stdout + r.stderr).strip().split('\n')[-4:]))

    # ⚠️ macro definida e nao usada e SINAL: ou e sobra do gerador, ou uma afirmacao foi
    # cortada do corpo. Nao reprova — informa, para eu conferir qual dos dois e.
    import re as _re
    _mac = (AQUI / 'regras_publicadas.tex')
    if _mac.exists():
        _defs = set(_re.findall(r'\\newcommand\{\\(\w+)\}', _mac.read_text(encoding='utf-8')))
        # ⛔ 21/09: a lista varria so os `sec_*.tex`, entao toda macro usada no RESUMO
        # (que vive no `main.tex`) ou no suplementar saia como «sem uso». O
        # `\\resRuidoN{}` do resumo reescrito hoje apareceu assim, e um detector que da
        # falso positivo e um detector que se aprende a ignorar. Varre onde as macros
        # podem legitimamente ser usadas.
        _corpo = ''.join((AQUI / x).read_text(encoding='utf-8') for x in (
            'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
            'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex',
            'main.tex', 'supplementary.tex', 'graphical_abstract.tex')
            if (AQUI / x).exists())
        _corpo += ''.join(q.read_text(encoding='utf-8')
                          for q in list(AQUI.glob('tab_*.tex')) + list(AQUI.glob('fig_*.tex')))
        # ⛔ 27/09, a MESMA licao de 21/09 uma camada abaixo: procurar so
        # `\\macro{}` e `\\macro ` nao acha `$\\macro$`, `\\macro}`, `\\macro,` nem
        # `\\macro/`, e o resumo grafico usa as quatro formas. Nove macros dele
        # saiam como «sem uso» estando em uso. A regra certa e a do LaTeX:
        # o nome termina onde acaba a sequencia de letras.
        _sem = sorted(k for k in _defs
                      if not _re.search(r'\\%s(?![A-Za-z])' % k, _corpo))
        if _sem:
            print('   ℹ️  %d macro(s) medida(s) sem uso no corpo: %s'
                  % (len(_sem), ', '.join(_sem)))

    for _sep in ('graphical_abstract', 'cover_letter'):
        _lg = (AQUI / (_sep + '.log'))
        if _lg.exists():
            e = sum(1 for l in _lg.read_text(errors='ignore').split('\n')
                    if l.startswith('!'))
            print('   %s %s (%d erro)' % ('✅' if not e else '⛔', _sep, e))

    mp, sp = paginas('main.pdf'), paginas('supplementary.pdf')
    log = (AQUI / 'main.log').read_text(errors='ignore')
    erros = sum(1 for l in log.split('\n') if l.startswith('!'))
    print('\n   main %d p   supl %d p   erros %d' % (mp, sp, erros))
    # ⛔ o teto era 30 e nao e: o [author] fixou 37 em 06/09/2026 («LIMITE EH 37 nao quero
    # mais 38 nem 39»), depois de ter levantado o de 30. Com o corpo em 31 a suite inteira
    # reprovava por um teto que nao vigora, e uma suite que reprova sempre nao e lida.
    TETO_DE_PAGINAS = 37
    if mp > TETO_DE_PAGINAS:
        print('   ⛔ o corpo passou de %d paginas' % TETO_DE_PAGINAS)
        falhou.append('teto de paginas')
    # ⭐ 21/09: a `ULTIMA-VERSAO/` passa a acompanhar o build em vez de ser copiada a mao.
    # Ela ficou com o TITULO ANTIGO e com o mesmo numero de paginas do atual, entao a
    # contagem nao denunciava; e o `fonte/` estava sem um `.tex` novo, ou seja, a pasta
    # nao compilava. ⛔ So roda com 0 erro de LaTeX: copiar PDF de build quebrado ja
    # aconteceu aqui uma vez.
    if not erros:
        try:
            import atualiza_ultima_versao as _uv
            r = _uv.sincroniza()
            print('   ✅ ULTIMA-VERSAO sincronizada: %d PDFs, %d fontes%s'
                  % (r['pdfs'], r['fontes'],
                     '' if not r['removidos'] else
                     ', %d removido(s) do fonte/' % len(r['removidos'])))
        except SystemExit as e:
            print('   ⛔ ULTIMA-VERSAO: %s' % e)
            falhou.append('ULTIMA-VERSAO')
    else:
        print('   ⏭  ULTIMA-VERSAO nao sincronizada: o build tem %d erro(s)' % erros)

    print('   %s' % ('✅ TUDO APROVA' if not falhou else '⛔ REPROVOU: ' + ', '.join(falhou)))
    if pendentes:
        print('   ⏳ aguardando o autor: %s' % ', '.join(pendentes))
    return 1 if falhou else 0


if __name__ == '__main__':
    sys.exit(main())
