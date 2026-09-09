#!/usr/bin/env python3
"""⛔ ALGUM NEGRITO E LONGO DEMAIS PARA DESTACAR ALGUMA COISA?

POR QUE EXISTE (08/09/2026). O revisor notou «blocos inteiros destacados que competem entre
si». A conclusao tinha tres negritos de **36, 36 e 21 palavras**; quando quase tudo esta em
negrito, nada esta. O destaque deve marcar a oracao que carrega o achado, nao o paragrafo.

⚠️ O limite de 20 palavras nao e arbitrario: e o tamanho acima do qual o destaque deixa de
caber numa linha e meia de coluna, que e onde o olho ainda o le como enfase.

Autoteste de duas pernas: um destaque curto passa e um de 30 palavras REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
LIMITE = 20
# ⛔ o `main.tex` entra pela lacuna medida em 09/09: e onde mora o RESUMO, que tem
# negrito e pode repetir frase do corpo, e nenhuma das duas guardas o abria.
ARQS = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex', 'sec_results.tex',
        'sec_discussion.tex', 'sec_conclusion.tex']
ARQS += [p.name for p in sorted(AQUI.glob('tab_*.tex')) + sorted(AQUI.glob('fig_*.tex'))]


def negritos(texto):
    t = re.sub(r'(?m)^\s*%.*$', '', texto)
    out = []
    for x in re.findall(r'\\textbf\{([^{}]{0,600})\}', t):
        limpo = re.sub(r'\\[a-zA-Z]+|[${}~\\]', ' ', x)
        out.append((len(limpo.split()), ' '.join(limpo.split())))
    return out


def confere(fontes=None):
    fontes = fontes or {f: (AQUI / f).read_text(encoding='utf-8')
                        for f in ARQS if (AQUI / f).exists()}
    longos = []
    for nome, txt in fontes.items():
        for n, s in negritos(txt):
            if n > LIMITE:
                longos.append((n, nome, s[:76]))
    return not longos, sorted(longos, reverse=True)


def _autoteste():
    ok, longos = confere()
    assert ok, '⛔ ja ha negrito longo: %s' % longos[:1]
    CURTO = {'x.tex': r'The count \textbf{dominates in every regime measured}, and the rest follows.'}
    LONGO = {'x.tex': r'\textbf{' + ' '.join('palavra%d' % i for i in range(30)) + '}'}
    assert confere(CURTO)[0], '⛔ reprovou um destaque curto'
    assert not confere(LONGO)[0], '⛔ NAO separa: um destaque de 30 palavras passou'
    print('  autoteste ✅ (destaque de 30 palavras REPROVA; um curto passa)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, longos = confere()
    print('  %d arquivos varridos, limite de %d palavras por destaque' % (len(ARQS), LIMITE))
    for n, nome, s in longos:
        print('    ⛔ %s (%d palavras) %s' % (nome, n, s))
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
