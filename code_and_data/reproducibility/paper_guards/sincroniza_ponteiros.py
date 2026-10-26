#!/usr/bin/env python3
"""⭐ SINCRONIZA OS PONTEIROS DO CORPO PARA O SUPLEMENTAR, a partir do que o LaTeX produziu.

POR QUE EXISTE (07/09/2026). Sao dois documentos separados, entao `\\ref` nao alcanca: o corpo
cita tabela do suplementar pelo NUMERO DIGITADO. E o numero muda toda vez que uma tabela entra
ou sai do suplementar. Isso aconteceu TRES vezes numa noite:
  - inserir a `tab_ct`  empurrou o rastreio de S17 para S18;
  - mover a `tab_screening` empurrou tudo de novo;
  - mover a `tab_e2e` empurrou pela terceira vez.
Nas tres o corpo continuou apontando para o numero velho, que EXISTIA — apontando para outra
tabela. Consertar a mao nao escala e ja errei uma vez.

COMO FUNCIONA: cada entrada liga um rotulo a um TRECHO do corpo que o cita. O script le o
`supplementary.aux`, acha o numero real e reescreve o numero na frase daquele trecho.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# rotulo -> trecho do corpo, unico, que contem o ponteiro daquele rotulo
ANCORA = {
    'tab:validation': 'the excerpt that fixes each reading',
    'tab:families': "reports each family's best value on each axis",
    'fig:inversion': 'repeats the same accuracies as a single',
    'tab:reuse': 'separates, for the cases that carry the claims here',
    'tab:reuse#2': 'so the comparison isolates the rule',
    'tab:trace': 'carries the correspondence',
    'tab:ct': 'visible in the equation before any measurement',
    'fig:menu': 'shows both distributions',
    'tab:screening': 'applies the same complete-case rule',
    'tab:e2e': 'reports the complete-operation comparison',
    'tab:e2e#2': 'scores each',
    'fig:direction': 'orders the eight',
    'fig:mechanism': 'shows the two together',
    'tab:coverage': 'per-test coverage is recorded',
    'tab:literature': 'puts all sixteen operations',
    'tab:inventory': 'the objective its source declares',
}


def numeros():
    a = (AQUI / 'supplementary.aux').read_text()
    return {m.group(1): m.group(2) for m in
            re.finditer(r'\\newlabel\{([^}]*)\}\{\{(S\d+)\}', a)}


def maior_tabela():
    a = (AQUI / 'supplementary.aux').read_text()
    n = [int(x) for x in re.findall(r'\\newlabel\{tab:[^}]*\}\{\{S(\d+)\}', a)]
    return max(n) if n else 0


def maior_figura():
    """O maior S de FIGURA no suplementar, lido do .aux que o LaTeX produziu."""
    n = [int(x) for x in re.findall(r'\\newlabel\{fig:[^}]*\}\{\{S(\d+)\}',
                                   (AQUI / 'supplementary.aux').read_text())]
    return max(n) if n else 0


def sincroniza(escreve=True):
    num, trocas = numeros(), []
    for nome in CORPO:
        p = AQUI / nome
        if not p.exists():
            continue
        s = orig = p.read_text()
        for rot, trecho in ANCORA.items():
            alvo = num.get(rot.split('#')[0])
            if not alvo:
                continue
            for m in re.finditer(re.escape(trecho), s):
                # a frase inteira em volta do trecho, para achar o ponteiro dela
                a = s.rfind('.', 0, max(0, m.start() - 200)) + 1
                b = s.find('.', m.end())
                frase = s[a:b + 1] if b > 0 else s[a:]
                nova = re.sub(r'((?:Table|Tables|Fig\.|Figure)~?)S\d+',
                              lambda x: x.group(1) + alvo, frase)
                if nova != frase:
                    s = s[:a] + nova + s[b + 1:] if b > 0 else s[:a] + nova
                    trocas.append((nome, rot, alvo))
        # As faixas guarda-chuva acompanham o maior numero real de CADA familia.
        # ⛔ Ate 08/09 esta linha trocava QUALQUER `S1--SN` pelo maior numero de TABELA, e
        # por isso reescreveu «Supplementary Figures S1--S4» como «S1--S26». A familia
        # agora entra no padrao, e cada uma le o seu proprio maximo.
        for palavra, maior in (('Tables', maior_tabela()), ('Figures', maior_figura())):
            alvo_faixa = f'{palavra} S1--S{maior}'
            s2 = re.sub(palavra + r'\s+S1\s*-{2,}\s*S\d+', alvo_faixa, s)
            if s2 != s:
                trocas.append((nome, 'faixa ' + palavra, alvo_faixa))
                s = s2
        if s != orig and escreve:
            p.write_text(s)
    return trocas


def _autoteste():
    """⭐ Duas pernas: rodar de novo nao muda nada, e um numero errado E corrigido."""
    sincroniza()
    assert not sincroniza(), '⛔ nao converge: a segunda passada ainda muda algo'
    p = AQUI / 'sec_method.tex'
    antes = p.read_text()
    num = numeros()['tab:trace']
    p.write_text(antes.replace(f'Table~{num} of the supplement carries',
                               'Table~S99 of the supplement carries'))
    t = sincroniza()
    assert any(r == 'tab:trace' for _, r, _ in t), '⛔ nao corrigiu o ponteiro quebrado'
    assert p.read_text() == antes, '⛔ nao restaurou exatamente o valor certo'
    return True


if __name__ == '__main__':
    assert _autoteste()
    t = sincroniza()
    print(f'  autoteste ✅ (corrige um S99 plantado e converge)')
    print(f'  {len(t)} ponteiro(s) sincronizado(s)' if t else '  ✅ ja estavam todos certos')
    for f, r, n in t:
        print(f'    {f}: {r} -> {n}')
    for rot, n in sorted(numeros().items()):
        if rot in ANCORA:
            print(f'    {rot:<16} = {n}')
    sys.exit(0)
