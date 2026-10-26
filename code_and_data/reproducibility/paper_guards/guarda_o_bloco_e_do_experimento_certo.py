#!/usr/bin/env python3
r"""⛔ A UNIDADE DE REAMOSTRAGEM DECLARADA E A DO EXPERIMENTO DAQUELE PARAGRAFO?

POR QUE EXISTE (23/09/2026, parecer v8, 2.1). A mesma REGRA de agrupamento (unir os dois
rotulos de topico que partilham os `.mp4`) vale nos dois experimentos, e por isso a
correcao anterior foi aplicada aos dois. ⛔ Mas os dois tem DADOS diferentes, logo
NUMEROS diferentes de bloco: 12 nas comparacoes construidas (de 13 rotulos) e 18 na
aplicacao (de 19). O paragrafo `The application estimand` do suplementar saiu dizendo
«resamples the \invBlocosN{} source-aware blocks», que e o numero do OUTRO experimento.

🔴 Nada reprovou. O numero vinha de macro, a macro vinha de arquivo, o arquivo estava
certo — e a frase estava errada, porque a macro era a do experimento errado. As guardas
de numero conferem VALOR contra FONTE; nenhuma conferia se a fonte e a que o paragrafo
nomeia. Quem achou foi um revisor humano, lendo a pagina.

⭐ A CHECAGEM. Nao e sobre a frase inteira: e sobre a ASSINATURA que declara uma unidade,
`resampl... the \MACRO`. Onde essa forma aparece, a macro tem de ser a do experimento do
paragrafo. O experimento sai do marcador que aparece PRIMEIRO no paragrafo.

⚠️ Porque nao pela frase: a redacao original dizia «the same convention the constructed
pairs use» DENTRO da mesma frase, entao qualquer regra que perdoasse frases que citam os
dois experimentos deixava passar exatamente o defeito que existe para pegar. ⛔ Uma
checagem que nao reprova o caso conhecido nao detecta nada.

Autoteste de duas pernas: o estado atual passa, e a REDACAO ORIGINAL DO DEFEITO reprova.
"""
import re
import sys
from pathlib import Path

A = Path(__file__).parent
ARQUIVOS = ['supplementary.tex'] + [p.name for p in sorted(A.glob('sec_*.tex'))] \
    + [p.name for p in sorted(A.glob('tab_*.tex'))]

MACROS = {
    'pares': {'invBlocos', 'invBlocosN'},
    'aplicacao': {'fusBlocos', 'senBlocos'},
}
# o que identifica cada experimento, sem se confundir com o outro
MARCA = {
    'pares': [r'\b800 pairs\b', r'\b20 segments\b', r'\bconstructed pairs\b',
              r'\bconstructed comparisons\b', r'\bconstructed benchmark\b'],
    'aplicacao': [r'\b42 clusters\b', r'\b42 operational clusters\b',
                  r'\brepresentative per cluster\b', r'\bthe application\b'],
}
# a assinatura de quem DECLARA uma unidade de reamostragem
DECLARA = re.compile(r'resampl\w*\s+(?:the\s+)?\\([A-Za-z]+)\s*\{\}')


def paragrafos(texto):
    t = '\n'.join(l for l in texto.splitlines() if not l.lstrip().startswith('%'))
    for bruto in re.split(r'\n\s*\n|\\paragraph\{', t):
        p = re.sub(r'\s+', ' ', bruto).strip()
        if p:
            yield p


def _experimento(p):
    """O experimento do paragrafo: o marcador que aparece PRIMEIRO nele."""
    pos = {}
    for exp, pats in MARCA.items():
        achados = [m.start() for q in pats for m in re.finditer(q, p)]
        if achados:
            pos[exp] = min(achados)
    return min(pos, key=pos.get) if pos else None


def confere(textos):
    ruins = []
    todas = set().union(*MACROS.values())
    for nome, texto in textos.items():
        for p in paragrafos(texto):
            exp = _experimento(p)
            if exp is None:
                continue
            for m in DECLARA.finditer(p):
                mac = m.group(1)
                if mac in todas and mac not in MACROS[exp]:
                    ruins.append((nome, mac, exp, p[max(0, m.start() - 70):m.end() + 40]))
    return ruins


def _lidos():
    return {n: (A / n).read_text(errors='replace') for n in ARQUIVOS if (A / n).exists()}


# a redacao exata que o revisor achou na pagina 40, para o controle nao depender da atual
DEFEITO = (r'\textbf{The primary interval resamples the \invBlocosN{} source-aware blocks}'
           r' and retains their clusters: the two topic labels that share source videos'
           r' count as one block, the same convention the constructed pairs use.')


def _autoteste():
    textos = _lidos()
    if confere(textos):
        return False, '⛔ o estado atual ja reprova'
    alvo = 'supplementary.tex'
    marca = 'For each operation the application selects one'
    if marca not in re.sub(r'\s+', ' ', textos[alvo]):
        return False, ('⛔ controle morto: o paragrafo do estimando da aplicacao mudou de '
                       'abertura, e o defeito historico nao tem mais onde ser plantado')
    ruim = dict(textos)
    # planta a REDACAO ORIGINAL do defeito no paragrafo onde ela esteve
    ruim[alvo] = re.sub(r'\\textbf\{The primary interval resamples.*?sampled label\.',
                        lambda _m: DEFEITO, textos[alvo], count=1, flags=re.S)
    if ruim[alvo] == textos[alvo]:
        return False, '⛔ controle morto: nao consegui plantar o defeito historico'
    if not confere(ruim):
        return False, '⛔ o defeito HISTORICO passou: a guarda nao pega o caso conhecido'
    return True, ''


if __name__ == '__main__':
    ok, msg = _autoteste()
    assert ok, msg
    print('  autoteste ✅ (a redacao original do «12 blocos na aplicacao» REPROVA)')
    ruins = confere(_lidos())
    for nome, mac, exp, trecho in ruins:
        print('  ⛔ %s: \\%s declara a unidade num paragrafo sobre «%s»' % (nome, mac, exp))
        print('       ...' + trecho)
    if ruins:
        print('  ⛔ %d unidade(s) declarada(s) com a contagem do experimento errado'
              % len(ruins))
        sys.exit(1)
    print('  ✅ cada unidade declarada usa a contagem do experimento do paragrafo')
