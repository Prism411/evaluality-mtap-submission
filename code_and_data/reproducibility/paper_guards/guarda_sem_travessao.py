#!/usr/bin/env python3
"""O [author] nao usa travessao. A correcao e reescrever a frase, nunca trocar por hifen.

Tres coisas escrevem '---' num fonte LaTeX e SO UMA viola a regra:

  1. comentario de fonte  '%% --- S1: tab:dataset ---'   nao renderiza, ignorar
  2. celula de tabela     '& --- &'  ou  '{---}'          marca de "sem valor", ignorar
  3. PROSA                'a energia---a razao e 0,95---e' <-- e esta que reprova

O titulo publicado de uma referencia (references.bib) tambem fica fora: mudar
o titulo de outro autor e citar errado a fonte.

Autoteste de duas pernas: aprova o mundo certo E reprova o defeito reintroduzido.
Uma guarda que passa nos dois mundos nao separa nada.
"""
import io, os, re, sys, glob

RAIZ = os.path.dirname(os.path.abspath(__file__))

# uma celula de tabela: o --- esta cercado por &, \\ ou {} e nada mais
# lookahead nos delimitadores: nao consome o '&' que separa duas celulas seguidas
CELULA = re.compile(r'(?<=[&{])\s*(?:\\[a-zA-Z]+(?:\{[^{}]*\})?\{)?\s*---\s*\}?\s*(?=[&}]|\\\\)')


# ⛔ BURACO MEDIDO EM 08/09 por `mutacao_da_suite.py`: a guarda cobria «---» e NAO o
# travessao UNICODE. Um «—» digitado direto compila igual e sai no PDF do mesmo jeito —
# e e justamente o que se digita sem perceber. O «–» entra junto: faixa em LaTeX e «--».
UNICODE = '\u2014\u2013'


def sites_de_prosa(texto):
    """Devolve [(n_linha, trecho)] dos travessoes que sao prosa, LaTeX ou Unicode."""
    achados = []
    for i, linha in enumerate(texto.split('\n'), 1):
        if linha.lstrip().startswith('%'):
            continue                                  # caso 1
        limpa = CELULA.sub(' CELULA ', linha)         # caso 2
        for m in re.finditer('---|[' + UNICODE + ']', limpa):
            ini = max(0, m.start() - 45)
            achados.append((i, limpa[ini:m.end() + 45].strip()))
    return achados


def varre():
    fontes = sorted(f for f in glob.glob(os.path.join(RAIZ, '*.tex')))
    tudo = []
    for f in fontes:
        for n, trecho in sites_de_prosa(io.open(f, encoding='utf-8').read()):
            tudo.append((os.path.basename(f), n, trecho))
    return fontes, tudo


def autoteste():
    """Perna 1: um texto limpo passa. Perna 2: o defeito reintroduzido REPROVA."""
    limpo = (
        "%% --- S1: tab:dataset ---\n"
        "A energia medida cai, a razao e $0.95$, e a resposta e $62.9$.\n"
        "Modulos reproduzidos & 2 & --- & --- & nao triado \\\\\n"
        "Informacao espacial & \\textcolor{black!45}{---} \\\\\n"
    )
    if sites_de_prosa(limpo):
        print("   autoteste ❌ perna 1: acusou travessao onde nao ha ->",
              sites_de_prosa(limpo))
        return False

    sujo = limpo.replace("A energia medida cai, a razao e $0.95$,",
                         "A energia medida cai---a razao e $0.95$---")
    if not sites_de_prosa(sujo):
        print("   autoteste ❌ perna 2: NAO reprovou o travessao de prosa reintroduzido")
        return False

    # ⛔ a perna que faltava, e que deixou a mutacao passar: o travessao UNICODE
    uni = limpo.replace("A energia medida cai,", "A energia medida cai \u2014")
    if not sites_de_prosa(uni):
        print("   autoteste ❌ perna 3: NAO reprovou o travessao UNICODE reintroduzido")
        return False

    print("   autoteste ✅ (aprova o limpo; reprova '---' E o travessao unicode)")
    return True


if __name__ == '__main__':
    if not autoteste():
        sys.exit(2)
    fontes, achados = varre()
    print("   %d arquivos .tex varridos" % len(fontes))
    if achados:
        print("   ❌ REPROVA: %d travessao(oes) de prosa" % len(achados))
        for arq, n, trecho in achados:
            print("      %s:%d  %s" % (arq, n, trecho))
        print("   corrija REESCREVENDO a frase, nao trocando por hifen.")
        sys.exit(1)
    print("   ✅ APROVA: nenhum travessao de prosa no corpo nem no suplementar")
