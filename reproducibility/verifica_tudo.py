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
PY = '/dados/Projetos/jl-summ-graph/.venv/bin/python'

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
        _corpo = ''.join((AQUI / x).read_text(encoding='utf-8') for x in (
            'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
            'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex'))
        _sem = sorted(k for k in _defs
                      if ('\\%s{}' % k) not in _corpo and ('\\%s ' % k) not in _corpo)
        if _sem:
            print('   ℹ️  %d macro(s) medida(s) sem uso no corpo: %s'
                  % (len(_sem), ', '.join(_sem)))

    ga = (AQUI / 'graphical_abstract.log')
    if ga.exists():
        e = sum(1 for l in ga.read_text(errors='ignore').split('\n') if l.startswith('!'))
        print('   %s graphical_abstract (%d erro)' % ('✅' if not e else '⛔', e))

    mp, sp = paginas('main.pdf'), paginas('supplementary.pdf')
    log = (AQUI / 'main.log').read_text(errors='ignore')
    erros = sum(1 for l in log.split('\n') if l.startswith('!'))
    print('\n   main %d p   supl %d p   erros %d' % (mp, sp, erros))
    if mp > 30:
        print('   ⛔ o corpo passou de 30 paginas')
        falhou.append('teto de paginas')
    print('   %s' % ('✅ TUDO APROVA' if not falhou else '⛔ REPROVOU: ' + ', '.join(falhou)))
    if pendentes:
        print('   ⏳ aguardando o autor: %s' % ', '.join(pendentes))
    return 1 if falhou else 0


if __name__ == '__main__':
    sys.exit(main())
