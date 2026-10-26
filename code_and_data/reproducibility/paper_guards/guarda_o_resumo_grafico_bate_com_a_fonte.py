#!/usr/bin/env python3
"""O resumo grafico nao digita numero: todos saem de `regras_publicadas.tex`.

⛔ POR QUE ESTA GUARDA EXISTE. Ate 27/09 NENHUMA guarda conferia numero do
resumo grafico contra a fonte. As que alcancavam a peca olhavam sobreposicao de
palavras, comando vazado, compilacao e sincronia do pacote -- nenhuma olhava o
que ela AFIRMA. A peca entao trazia onze numeros digitados a mao, entre eles um
`22/42` que ja nao estava no resumo nem na conclusao do artigo, e barras com
comprimento multiplicado a mao (`65.1 % x 6.55 = 4.26`) que nao acompanhavam a
macro. Ela envelheceu em silencio enquanto o artigo mudava.

As tres pernas, porque nenhuma sozinha basta:

  A. TEXTO DE NO nao contem algarismo. Pega o numero digitado a mao MESMO
     QUANDO O VALOR ESTA CERTO -- que era o caso dos onze. As outras duas
     pernas nao pegam isso: um `800` digitado confere com \\parConstruidos.
  B. Todo numero IMPRESSO no PDF e valor de alguma macro. Pega o numero que
     derivou da fonte, e pega tambem o que veio de conta feita no .tex.
  C. Toda macro declarada aparece no .tex E, se for de imprimir, seu valor sai
     no PDF. Pega o que SUMIU: apagar um painel nao quebra nada nas pernas A e
     B, porque elas so olham o que ficou.

⚠️ A TAXA BASE DA PERNA B E ALTA, e isso fica dito porque o ✅ nao pode prometer
mais do que entrega: contra os 136 valores de macro do artigo, **90 % dos
digitos de 0 a 9 e 33 % dos numeros de dois digitos passariam por acaso**. Para
numero pequeno, o ✅ de B quase nao e evidencia -- quem separa e a perna A, que
nao olha o VALOR e sim se o numero foi digitado. B so tem forca de verdade nos
tres digitos (1 %), onde moram o 797 e o 800.
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
TEX = AQUI / 'graphical_abstract.tex'
PDF = AQUI / 'graphical_abstract.pdf'
REGRAS = AQUI / 'regras_publicadas.tex'

# ⭐ as macros que a peca TEM de continuar imprimindo. Lista declarada, nao
# deduzida do arquivo: guarda que le a lista do proprio alvo aprova qualquer
# coisa que o alvo resolva virar.
MACROS_IMPRESSAS = [
    # ⭐ 27/09: o desenho novo imprime QUATRO numeros medidos, nao doze. As
    # macros dos paineis antigos continuam existindo em regras_publicadas e
    # aparecem na lista de «sem uso» do verifica_tudo, que e onde devem estar:
    # entrada morta numa lista de guarda reprova por fato, nao por defeito.
    'resElegiveisN', 'invModelosN',          # 3/10 modelos dedicados passam
    'triagemPassam', 'fontesDaLiteraturaN',  # 0/15 operacoes passam
    'resRuidoN',                             # 13/15 preferem a copia ruidosa
    'disOps', 'disResumos',                  # 21 -> 18 selecoes distintas
]
MACROS_DE_DESENHO = []

# ⚠️ os UNICOS algarismos digitados na peca: a numeracao das quatro etapas.
# Nao sao medicao, e a perna D abaixo prende exatamente onde eles moram, para
# que ninguem contrabandeie um numero medido como «passo».
ENUMERACAO = {'1', '2', '3', '4'}
PASSOS_ESPERADOS = ('1/{Lifted out}', '2/{The test}', '3/{Why}', '4/{Consequence}')

# numero solto: nem precedido de letra/digito/ponto, nem colado a letra depois.
# ⚠️ o `H.264` do painel 1 e TEXTO com algarismo e sai por esta janela, como
# deve: ele e rotulo de tipo, nao afirmacao medida.
NUM = re.compile(r'(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)(?![0-9.]*[A-Za-z])')


def sem_comentario(t):
    return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('%'))


def textos_de_no(tex):
    """Os corpos de texto dos \\node: o que a peca AFIRMA, sem a geometria.

    Pula os `[...]` de opcao e os `(...)` de coordenada e devolve o grupo entre
    chaves que sobra -- que e o unico lugar onde um numero digitado seria lido
    pelo leitor.
    """
    t = sem_comentario(tex)
    saida = []
    for m in re.finditer(r'\\node\b', t):
        i = m.end()
        while i < len(t):
            if t[i] in ' \n\t':
                i += 1
            elif t[i] == '[':
                d = 0
                while i < len(t):
                    d += (t[i] == '[') - (t[i] == ']')
                    i += 1
                    if d == 0:
                        break
            elif t[i] == '(':
                i = t.index(')', i) + 1
            elif t[i:i + 2] == 'at':
                i += 2
            elif t[i] == '{':
                d, ini = 0, i
                while i < len(t):
                    d += (t[i] == '{') - (t[i] == '}')
                    i += 1
                    if d == 0:
                        break
                saida.append(t[ini + 1:i - 1])
                break
            else:
                break
    return saida


def valores_das_macros():
    """Todo numero que aparece no corpo de alguma macro medida."""
    vals = set()
    for m in re.finditer(r'\\newcommand\{\\[A-Za-z]+\}\{(.*)\}', REGRAS.read_text()):
        vals.update(NUM.findall(m.group(1)))
    return vals


def numeros_do_pdf():
    txt = subprocess.run(['pdftotext', str(PDF), '-'],
                         capture_output=True, text=True, check=True).stdout
    return NUM.findall(txt)


def confere(tex=None):
    """As pernas A e D leem o TEXTO (proprio ou mutado); B e C leem o PDF.

    ⛔ 27/09: aqui havia um `return` antecipado quando `tex` nao era o arquivo
    real, «para o autoteste rodar sem PDF». Ele fazia a perna D nunca rodar no
    mutante, e a perna D passou no autoteste sem poder reprovar. Agora a
    separacao e explicita: o que depende do PDF roda so no estado real.
    """
    real = tex is None
    tex = TEX.read_text() if real else tex
    ruins = []

    # --- A: nenhum algarismo no texto dos nos -------------------------------
    for corpo in textos_de_no(tex):
        limpo = re.sub(r'\\[A-Za-z]+', ' ', corpo)
        for n in NUM.findall(limpo):
            ruins.append('A: numero «%s» DIGITADO no texto de um no: «%s»'
                         % (n, ' '.join(corpo.split())[:70]))

    # --- D: os algarismos digitados sao SO a numeracao das etapas -----------
    compacto = re.sub(r'\s+', '', tex)
    for passo in PASSOS_ESPERADOS:
        if re.sub(r'\s+', '', passo) not in compacto:
            ruins.append('D: a etapa «%s» sumiu ou mudou de numero; a excecao '
                         'de enumeracao so vale para estas quatro' % passo)

    if not real:
        return not ruins, ruins

    # --- B: todo numero impresso e valor de macro ---------------------------
    macros, saida = valores_das_macros(), numeros_do_pdf()
    for n in sorted(set(saida)):
        if n in ENUMERACAO:
            continue
        if n not in macros:
            ruins.append('B: o PDF imprime «%s», que nao e valor de macro '
                         'nenhuma de regras_publicadas.tex' % n)

    # --- C: nada sumiu ------------------------------------------------------
    reg = REGRAS.read_text()
    for nome in MACROS_IMPRESSAS + MACROS_DE_DESENHO:
        if ('\\' + nome) not in tex:
            ruins.append('C: a macro \\%s sumiu do resumo grafico' % nome)
            continue
        if nome in MACROS_DE_DESENHO:
            continue
        v = re.search(r'\\newcommand\{\\%s\}\{(.*)\}' % nome, reg)
        assert v, '⛔ \\%s nao existe em regras_publicadas.tex' % nome
        faltam = [x for x in NUM.findall(v.group(1)) if x not in saida]
        if faltam:
            ruins.append('C: \\%s vale «%s» e o PDF nao imprime %s'
                         % (nome, v.group(1)[:40], faltam[:4]))
    return not ruins, ruins


def autoteste():
    ok, ruins = confere()
    if not ok:
        print('    ⛔ autoteste: o estado atual ja reprova: %s' % ruins[:3])
        return False
    # ⛔ a perna que separa, na REDACAO HISTORICA: era assim que a peca trazia o
    # `800` a mao, e o valor estava CERTO -- um controle com numero inventado
    # nao exercita o defeito que de fato aconteceu.
    doente = (TEX.read_text()
              + '\n\\node[anchor=west] at (0,0) {Accuracy on the same 800 pairs};\n')
    if confere(doente)[0]:
        print('    ⛔ autoteste: aprovou um «800» digitado a mao no texto de um no')
        return False
    # ⚠️ e a perna do rotulo com algarismo que e TEXTO, nao afirmacao: o painel 1
    # imprime «H.264» e isso nao pode acusar.
    salvo = (TEX.read_text()
             + '\n\\node[anchor=west] at (0,0) {H.264 and AV1 are both tested};\n')
    if not confere(salvo)[0]:
        print('    ⛔ autoteste: acusou «H.264», que e rotulo de tipo, nao numero medido')
        return False
    # ⛔ e a perna D, exercitada: renumerar uma etapa tem de reprovar. Sem este
    # teste a excecao de enumeracao seria um buraco por onde qualquer algarismo
    # passaria dizendo-se «passo».
    # ⚠️ sem a coordenada: o alvo era `3/{Why}/944` e o desenho novo poe a etapa
    # em 957, entao a mutacao deixou de aplicar e o controle passou a «aprovar»
    # sem ter mudado nada. Controle que nao muda o mundo nao e controle -- o
    # assert abaixo garante que ele mudou.
    mutante = TEX.read_text().replace('3/{Why}', '7/{Why}')
    assert mutante != TEX.read_text(), (
        '⛔ a mutacao da etapa nao encontrou o alvo: o controle da perna D nao '
        'esta exercitando nada')
    if confere(mutante)[0]:
        print('    ⛔ autoteste: aprovou uma etapa renumerada de 3 para 7')
        return False
    print('   autoteste ✅ (reprova numero digitado a mao mesmo com valor certo; '
          'aceita rotulo com algarismo; pega etapa renumerada)')
    return True


if __name__ == '__main__':
    if not autoteste():
        sys.exit(1)
    ok, ruins = confere()
    v = valores_das_macros()
    _b = sum(1 for x in range(10) if str(x) in v)
    print('  %d numeros impressos conferidos contra %d valores de macro'
          % (len(set(numeros_do_pdf())), len(v)))
    print('  ⚠️ taxa base da perna B: %d dos 10 digitos passariam por acaso; '
          'quem separa numero pequeno e a perna A' % _b)
    for x in ruins[:8]:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA: o resumo grafico nao digita numero' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
