#!/usr/bin/env python3
r"""⛔ A REDACAO NOVA ENTROU SEM RETIRAR A ANTIGA?

POR QUE EXISTE (15/09/2026). Substitui uma frase do metodo e deixei a abertura da anterior:

    «The search instrument was itself measured against a manual reading of 21 articles: the
     search achieved recall of .81 and precision of .63 against a manual assessment of 21
     articles.»

Os **21 artigos** aparecem duas vezes na mesma frase. Foi um revisor humano que viu.

🔴 Ja aconteceu antes, com outro alvo: «the substitution is declared here and the
substitution is identified here» na nota da S22. **A assinatura e sempre a mesma** — a
mesma quantidade medida dita duas vezes dentro de uma frase.

⭐ A guarda: nenhuma frase do corpo repete a MESMA macro medida.

⛔ 21/09: a isencao `('sec_results.tex', 'jusAuditadas')` FOI RETIRADA. Ela cobria
«\jusAuditadas{} belong ... and all \jusAuditadas{} fail», declarada legitima porque a
repeticao afirmava que o subconjunto era o conjunto inteiro. **Mas a mesma frase digitava
«Of the same fourteen» enquanto \jusAuditadas + \jusSoJusante somavam VINTE**, e a isencao
mantinha a guarda calada justamente ali. A frase foi reescrita para «all of them» e a
isencao morreu junto. ⭐ Isencao posta para acomodar defeito e defeito, e isencao que nao
cobre mais nada tem de sair, senao ela volta a abrigar a proxima redacao ruim.
"""
import re, sys
from pathlib import Path

A = Path(__file__).parent
CORPO = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# repeticoes que AFIRMAM alguma coisa, e por isso ficariam. ⛔ Vazio desde 21/09: ver o
# cabecalho. Toda entrada aqui precisa cobrir uma frase que EXISTE no corpo; o autoteste
# abaixo reprova entrada morta.
ISENTAS = set()


def repetidas(textos=None):
    fontes = textos if textos is not None else {
        f: (A / f).read_text(encoding='utf-8') for f in CORPO if (A / f).exists()}
    ruins = []
    for f, t in fontes.items():
        t = re.sub(r'(?m)^%.*$', '', t)
        for frase in re.split(r'(?<=\.)\s', re.sub(r'\s+', ' ', t)):
            macros = re.findall(r'\\([a-zA-Z]+)\{\}', frase)
            for m in {x for x in macros if macros.count(x) > 1}:
                if (f, m) in ISENTAS:
                    continue
                ruins.append((f, m, frase.strip()[:96]))
    return ruins


def isencoes_mortas(quais=None):
    """As isencoes que nao suprimem nada: tirar cada uma tem de AUMENTAR o numero de
    frases acusadas. A que nao aumenta nao cobre caso nenhum e precisa sair."""
    global ISENTAS
    guardadas = set(ISENTAS)
    alvo = guardadas if quais is None else set(quais)
    mortas = []
    try:
        for e in sorted(alvo):
            ISENTAS = alvo - {e}
            sem = len(repetidas())
            ISENTAS = alvo
            if sem == len(repetidas()):
                mortas.append(e)
    finally:
        ISENTAS = guardadas
    return mortas


def main():
    r = repetidas()
    if r:
        print(f'  ⛔ {len(r)} frase(s) repetem a mesma macro medida:')
        for f, m, s in r:
            print(f'       {f}: \\{m}{{}} duas vezes em «{s}...»')
        print('     provavel redacao nova inserida sem retirar a anterior.')
        return 1
    print('  ✅ nenhuma frase do corpo diz a mesma quantidade medida duas vezes')
    return 0


def autoteste():
    mal = 0
    n = len(repetidas())
    print(f"  {'✅' if n == 0 else '⛔'} corpo atual: {n} repeticao(oes), esperado 0")
    mal += n != 0
    # ⛔ o defeito real de 15/09, replantado
    doente = {'x.tex': 'The search instrument was itself measured against a manual reading '
                       'of \\varrN{} articles: the search achieved recall of \\varrCob{} and '
                       'precision of \\varrPrec{} against a manual assessment of \\varrN{} '
                       'articles.'}
    n = len(repetidas(doente))
    print(f"  {'✅' if n == 1 else '⛔'} a frase duplicada dos 21 artigos: {n}, esperado 1")
    mal += n != 1
    # ⚠️ a perna que separa: a mesma macro em frases DIFERENTES nao e defeito
    ok = {'x.tex': 'It reads \\varrN{} articles. A second pass reads \\varrN{} again.'}
    n = len(repetidas(ok))
    print(f"  {'✅' if n == 0 else '⛔'} a mesma macro em duas frases: {n}, esperado 0")
    mal += n != 0
    # ⛔ 21/09: ISENCAO MORTA REPROVA. Uma isencao que nao suprime nada nao esta protegendo
    # um caso legitimo: esta esperando para abrigar a proxima redacao ruim naquele arquivo.
    mortas = isencoes_mortas()
    print(f"  {'✅' if not mortas else '⛔'} isencoes mortas no corpo: "
          f"{len(mortas)}, esperado 0{'' if not mortas else ' -> ' + str(mortas)}")
    mal += bool(mortas)
    # ⛔ e o controle que impede o ✅ acima de ser vazio: com ISENTAS hoje em branco, o teste
    # passaria sem olhar nada. Planto uma isencao que nao cobre frase nenhuma e exijo que
    # ela seja acusada.
    n = len(isencoes_mortas({('sec_results.tex', 'macroQueNaoExiste')}))
    print(f"  {'✅' if n == 1 else '⛔'} isencao morta plantada: {n}, esperado 1")
    mal += n != 1
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
