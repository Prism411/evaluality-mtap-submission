#!/usr/bin/env python3
r"""⛔ O NUMERO RESOLVE, MAS A TABELA E DE OUTRO ASSUNTO.

POR QUE EXISTE (14/09/2026, fim da tarde). Tres ponteiros do corpo nomeavam a tabela errada
e sobreviveram a nove rodadas de revisao:
  - «database-level correlations ... Table S15» e «the latter reports training-database
    contrasts»: a S15 e condicionamento por keypoint; os contrastes entre bases sao a S14;
  - «Tables S15 and S16 retain those diagnostics»: a S16 e o inventario das operacoes;
  - «the full prediction and overlay audits are in Tables S11 and S29»: a S29 e a
    reimplementacao independente, e **nao existe tabela de overlays** — o resultado de
    overlay esta DENTRO da S11.

🔴 Por que nada pegou. A `guarda_ponteiros_ao_suplementar` confere que o numero EXISTE e o
`sincroniza_ponteiros` mantem o numero de cada ancora DECLARADA em dia. Nenhum dos dois olha
para o ASSUNTO: um ponteiro sem ancora declarada nunca e conferido, e um numero valido que
aponta para outra tabela passa nas duas.

⭐ A regra: cada entrada liga o TRECHO do corpo que faz a promessa ao termo que a legenda da
tabela citada tem de conter. Se o corpo promete contrastes entre bases, a legenda apontada
tem de falar de contraste entre bases. ⚠️ E uma entrada que nao casa frase nenhuma REPROVA,
para nao envelhecer junto com o texto.
"""
import re, sys
from pathlib import Path

A = Path(__file__).parent
CORPO = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# (trecho do corpo que promete, termo que a legenda da tabela citada tem de conter)
# O numero da tabela sai da propria frase; o assunto, da legenda no `.tex` que a define.
PROMESSAS = [
    ('registered prediction audit',                     r'predictions registered'),
    # ⚠️ 21/09: «varies the numerical thresholds» virou «varies the thresholds and
    #    the quantifier» na reescrita. Mesmo ponteiro, mesma tabela.
    # ⚠️ 22/09: a reescrita do parecer v3 condensou a frase para «Threshold sensitivity
    #    is reported in». Mesmo ponteiro, mesma tabela, mesmo assunto.
    ('Threshold sensitivity is reported in',           r'generalization threshold'),
    ('recomputes every interval under the rival unit',  r'[Rr]esampling unit'),
    # ⛔ 21/09: a entrada trazia o NUMERO dentro da frase-ancora (`Table~S28 lists the`), e
    # o numero e exatamente o que o `sincroniza_ponteiros` existe para mover. Quando a
    # tabela de elegibilidade subiu para o corpo, `tab:inversoes` foi de S28 para S27 e a
    # entrada deixou de casar: a guarda reprovou a si mesma. Ancora nao carrega numero.
    ('lists the \\invCelulas{} cells with the',           r'below the 50 per cent chance floor'),
]


def _corpo():
    return {n: (A / n).read_text(encoding='utf-8', errors='replace')
            for n in CORPO if (A / n).exists()}


def _legendas():
    """numero S -> legenda, lida do .tex que define o rotulo e do .aux do suplementar."""
    aux = A / 'supplementary.aux'
    if not aux.exists():
        return None
    num = {m.group(1): m.group(2) for m in
           re.finditer(r'\\newlabel\{([^}]+)\}\{\{(S\d+)\}', aux.read_text(errors='replace'))}
    caps = {}
    for q in sorted(A.glob('*.tex')):
        t = q.read_text(errors='replace')
        for m in re.finditer(r'\\label\{((?:tab|fig):[^}]+)\}', t):
            j = t.rfind('\\caption', 0, m.start())
            if j < 0:
                continue
            caps[m.group(1)] = re.sub(r'\s+', ' ', t[j:m.start()])
    saida = {}
    for rot, n in num.items():
        if rot in caps:
            saida.setdefault(n, '')
            saida[n] += ' ' + caps[rot]
    return saida


def erradas(docs=None, caps=None):
    docs = _corpo() if docs is None else docs
    caps = _legendas() if caps is None else caps
    if caps is None:
        return []
    ruins = []
    for promessa, termo in PROMESSAS:
        pat = re.compile(r'\s+'.join(re.escape(w) for w in promessa.split()))
        achou = False
        for nome, t in docs.items():
            for m in pat.finditer(t):
                achou = True
                # o numero citado na mesma frase
                ini = max(t.rfind('.', 0, m.start()), 0)
                fim = t.find('.', m.end())
                frase = t[ini:fim if fim > 0 else len(t)]
                alvos = re.findall(r'(S\d+)', frase)
                if not alvos:
                    ruins.append((promessa[:44], '-', 'a frase nao cita tabela nenhuma'))
                    continue
                if not any(re.search(termo, caps.get(a, ''), re.I) for a in alvos):
                    ruins.append((promessa[:44], ','.join(alvos),
                                  'nenhuma legenda fala de «%s»' % termo))
        if not achou:
            ruins.append((promessa[:44], '-', 'entrada declarada que nao casa frase nenhuma'))
    return ruins


def main():
    r = erradas()
    if r:
        print(f'  ⛔ {len(r)} ponteiro(s) nomeiam tabela de outro assunto:')
        for p_, a, por in r:
            print(f'       «{p_}...» -> {a}: {por}')
        return 1
    print(f'  ✅ as {len(PROMESSAS)} promessas declaradas batem com a legenda que citam')
    return 0


def autoteste():
    docs, caps = _corpo(), _legendas()
    mal = 0
    n = len(erradas(docs, caps))
    print(f"  {'✅' if n == 0 else '⛔'} o corpo atual: {n} erro(s), esperado 0")
    mal += n != 0
    # ⛔ o defeito real de 14/09 replantado: o numero certo trocado por outro que EXISTE
    doente = dict(docs)
    doente['sec_results.tex'] = doente['sec_results.tex'].replace(
        'three-database exposure contrasts in\nTable~S14', 'three-database exposure contrasts in\nTable~S15')
    n = len(erradas(doente, caps))
    print(f"  {'✅' if n >= 1 else '⛔'} S14 trocada pela S15, que existe: {n} erro(s), esperado >=1")
    mal += n < 1
    # ⚠️ e a perna que separa: uma legenda que fala do assunto nao pode ser reprovada
    n = len(erradas(docs, dict(caps, S14='blah three-database contrasts blah')))
    print(f"  {'✅' if n == 0 else '⛔'} legenda minima mas correta: {n}, esperado 0")
    mal += n != 0
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
