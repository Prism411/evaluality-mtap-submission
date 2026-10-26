#!/usr/bin/env python3
r"""⛔ A TABELA 6 E A FIGURA S4 DIZEM O MESMO SOBRE A MESMA OPERACAO?

POR QUE EXISTE (22/09/2026, parecer v4, ponto 2.5). A Tabela 6 marcava `n/a` na retencao de
sete operacoes, e a legenda define `n/a` como **teste que nao se aplica aquela linha**. Mas
a Figura S4 mostrava a retencao delas, medida. O `n/a` estava dizendo «nao medido NESTE
arquivo», que e outra coisa: a figura complementa com o caminho publicado e a tabela nao.

⛔ O leitor via `n/a` numa peca e um numero na outra, para a mesma celula, sem nada que
explicasse a diferenca. ⚠️ E nenhuma guarda comparava as duas pecas.

⚠️ ALCANCE DECLARADO: o leitor casa pelos rotulos impressos e hoje cruza 4 operacoes
das 19 linhas de componente, porque a Tabela 6 agrupa por trabalho e nem toda linha traz
um rotulo que a figura tambem use. **Ela cobre a classe de defeito, nao a tabela inteira**;
quem ampliar o leitor deve conferir o autoteste, que mede quantas operacoes cruzam.

⭐ COMO SEPARA: le a coluna de retencao da Tabela 6 e os rotulos da Figura S4 e exige que,
para toda operacao presente nas duas, ou os valores batam, ou a tabela diga `n/a` E a
figura tambem nao a traga. Um `n/a` contra um numero REPROVA.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent


def _linhas_tabela():
    """rotulo -> ultima celula da linha (a retencao a jusante)."""
    t = (AQUI / 'tab_sintese.tex').read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(r'(?m)^(?:\\rowcolor\{[^}]*\})?([A-Z][A-Za-z0-9 +.\-()]{2,28})\s*&(.*?)\\\\', t, re.S):
        nome = m.group(1).strip()
        cels = [re.sub(r'\\cellcolor\{[^}]*\}|\\textcolor\{[^}]*\}|\\tiny|\\textbf|[{}$]', '', c).strip()
                for c in m.group(2).split('&')]
        if cels:
            out[nome] = cels[-1]
    return out


def _figura():
    """rotulo -> valor impresso na Figura S4."""
    t = (AQUI / 'fig_jusante.tex').read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(r'\{([A-Z][A-Za-z0-9 +.\-()]{2,28})\};', t):
        out[m.group(1).strip()] = True
    return out


def confere():
    tab, fig = _linhas_tabela(), _figura()
    ruins = []
    for nome, cel in tab.items():
        if nome in fig and 'n/a' in cel:
            ruins.append((nome, cel, 'aparece medida na Figura S4'))
    return ruins, len(tab), len(fig)


def _autoteste():
    """⛔ o controle: um `n/a` plantado numa operacao que a figura traz tem de REPROVAR."""
    tab, fig = _linhas_tabela(), _figura()
    comuns = [n for n in tab if n in fig and 'n/a' not in tab[n]]
    assert comuns, '⛔ nenhuma operacao nas duas pecas: o leitor esta quebrado'
    assert not confere()[0], '⛔ ja ha discordancia: %s' % confere()[0][:2]
    salvo = tab[comuns[0]]
    tab[comuns[0]] = 'n/a'
    plantado = [(n, c, '') for n, c in tab.items() if n in fig and 'n/a' in c]
    assert plantado, '⛔ NAO DISCRIMINA: o n/a plantado contra um valor da figura passou'
    print('  autoteste ✅ (%d operacoes nas duas pecas; n/a plantado REPROVA)' % len(comuns))
    return True


if __name__ == '__main__':
    assert _autoteste()
    r, nt, nf = confere()
    for nome, cel, por in r:
        print('  ⛔ %s: tabela diz %r mas %s' % (nome, cel, por))
    print('  %d linhas na Tabela 6, %d rotulos na Figura S4  |  %s' % (
        nt, nf, '✅ APROVA' if not r else '⛔ %d celula(s) discordam' % len(r)))
    sys.exit(0 if not r else 1)
