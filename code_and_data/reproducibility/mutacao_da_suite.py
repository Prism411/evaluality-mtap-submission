#!/usr/bin/env python3
"""⭐⭐ QUANTOS DEFEITOS REAIS A SUITE DE 23 GUARDAS PEGA?

POR QUE EXISTE (08/09/2026). Vinte e tres guardas passando ✅ diz que nada QUEBROU. Nao diz
que elas PEGARIAM alguma coisa. A unica forma de saber e reintroduzir defeito e ver se
reprova — e fazer isso guarda a guarda, no autoteste, nao cobre o caso em que a suite
inteira olha para o lado.

Aqui cada mutacao e um defeito que ja aconteceu neste artigo ou que aconteceria: um digito
trocado, um travessao, uma limitacao apagada, um DOI com um digito a mais, uma faixa
desatualizada. A suite roda em COPIA e tem de REPROVAR em todas.

⚠️ Uma mutacao que a suite NAO pega nao e falha do teste: e um buraco medido, e o valor
deste arquivo esta justamente em nomear os buracos.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
# ⚠️ o diretorio de trabalho leva o PID: duas rodadas simultaneas usavam o MESMO caminho,
# e uma apagava a copia da outra no meio — o placar saiu com guarda trocada e um traceback.
TMP = Path('/tmp/claude-1000/-home-author-Desktop-estudos-workspace-notes/'
           '51d375ec-33aa-4092-b28f-309cfe691890/scratchpad/mut-%d' % os.getpid())
PY_ = '/data/projects/pipeline/.venv/bin/python'


def sub_um(p, velho, novo):
    """Uma substituicao. Devolve o par (aplicar, ainda_esta_la).

    ⚠️ Casa com espaco em branco flexivel: o `.tex` quebra frase em varias linhas, e
    comparar literal fez uma mutacao nao encontrar um alvo que existe.
    ⚠️ E falha alto se o alvo nao existe: mutacao que nao aplicou daria «a suite nao
    pegou» sem defeito nenhum plantado.
    """
    pad = re.compile(r'\s+'.join(re.escape(w) for w in velho.split()))
    npad = re.compile(r'\s+'.join(re.escape(w) for w in novo.split())) if novo.strip() else None

    def aplicar(raiz):
        a = raiz / p
        t = a.read_text(encoding='utf-8')
        assert pad.search(t), '⛔ a mutacao nao encontrou o alvo em %s: %r' % (p, velho[:40])
        a.write_text(pad.sub(lambda m: novo, t, count=1), encoding='utf-8')

    def ainda_esta_la(raiz):
        t = (raiz / p).read_text(encoding='utf-8')
        return bool(npad.search(t)) if npad else True

    return aplicar, ainda_esta_la


def regex_um(p, pad_, novo):
    pat = re.compile(pad_)

    def aplicar(raiz):
        a = raiz / p
        t = a.read_text(encoding='utf-8')
        assert pat.search(t), '⛔ a mutacao nao encontrou o padrao em %s: %r' % (p, pad_)
        a.write_text(pat.sub(novo, t, count=1), encoding='utf-8')

    def ainda_esta_la(raiz):
        # ⛔ conferia so o PRIMEIRO token do novo texto, e «Tables» esta sempre la: por
        # isso a faixa reparada aparecia como «escapou». Agora confere o texto inteiro.
        return novo in (raiz / p).read_text(encoding='utf-8')

    return aplicar, ainda_esta_la


MUTACOES = [
    ('um travessao na prosa',
     sub_um('sec_intro.tex', 'the degraded copy higher', 'the degraded copy — higher')),
    ('o IC da manchete volta a ser o por par',
     sub_um('sec_results.tex', '$[+29.8,+38.9]$', '$[+31.1,+37.7]$')),
    ('uma limitacao apagada da 5.1',
     regex_um('sec_discussion.tex', r'\\textbf\{No human judged these segments\}', 'Segments were selected')),
    ('um DOI com um digito trocado',
     sub_um('references.bib', '10.1109/CVPR52733.2024.02408', '10.1109/CVPR52733.2024.02409')),
    ('a faixa do suplementar desatualizada',
     regex_um('main.tex', r'Tables S1--S\d+', 'Tables S1--S16')),
    ('o resumo estourando o limite de palavras',
     regex_um('main.tex', r'\\abstract\{', r'\\abstract{' + ('padding word ' * 60))),
    # ⚠️ o alvo antigo desta linha era «chance floor of $47.0$», que ESTA lista mediu
    # como buraco em 08/09 e que virou macro `\dupPiso`. A classe fechou por construcao,
    # entao a mutacao passa a atacar outro decimal ainda digitado na prosa.
    # ⚠️ O ALVO MIGRA a cada vez que um decimal digitado vira macro. Fecharam em 08/09:
    # os tres da manchete (65,1 / 99,5 / +34,4), os tres do DOVER-T (50,5 / 76,0 / +25,5),
    # o piso de acaso 47,0 e a anticorrelacao -1,0000 do CT.
    # ⭐ A CLASSE FECHOU em 08/09: nao ha mais decimal digitado na prosa dos resultados.
    # Esta linha ataca um numero que agora vem de macro, entao ela deixa de encontrar o
    # alvo — e isso e o sinal certo. Passa a atacar o SUPLEMENTAR, onde ainda ha.
    ('um digito da tabela dos pares construidos',
     sub_um('sec_results.tex', 'TOPIQ & 93 & 100', 'TOPIQ & 39 & 100')),
    ('a media de uma linha da tabela dos pares',
     sub_um('sec_results.tex', 'BRISQUE & 100 & 100 & 100 & 99 & 100',
            'BRISQUE & 100 & 100 & 100 & 89 & 100')),
    ('uma frase repetida palavra por palavra',
     sub_um('sec_conclusion.tex', 'A blind pairwise judgment',
            'White noise concentrates the failures. These operations are statistics of '
            'local structure such as gradient magnitude, edge density, entropy, contrast '
            'and descriptor counts, and additive noise raises such statistics. '
            'A blind pairwise judgment')),
    ('a contagem das fontes contradizendo a proveniencia',
     sub_um('sec_method.tex', '\\fontesTrabalhos{} source works', 'nine source works')),
    ('uma remissao a secao que nao existe',
     sub_um('sec_results.tex', '(Section~\\ref{sec:menu})', '(Section~\\ref{sec:naoexiste})')),
    # ⭐ as duas ultimas fecham buracos que ESTA lista mediu em 08/09
    ('o travessao unicode, que a guarda so pegava em LaTeX',
     sub_um('sec_related.tex', 'The modular design enables',
            'The modular \u2014 design enables')),
    ('a contagem de fontes errada em UM dos tres lugares',
     sub_um('sec_intro.tex', 'from eleven source works', 'from nine source works')),
    # ⭐ as proximas existem para EXERCITAR guardas que a lista nunca tinha tocado: uma
    # guarda que nunca foi posta a prova por uma mutacao e uma guarda de que so se sabe
    # que roda, nao que separa.
    ('uma contradicao entre duas secoes',
     sub_um('sec_method.tex',
            'Ten of the eleven source works were read in full for this dimension',
            'All eleven source works were read in full for this dimension')),
    ('uma excecao nomeada que nao fecha com a conta',
     sub_um('sec_method.tex', 'the exception is \\citet{xu2024property}',
            'the exceptions are \\citet{xu2024property} and one other')),
    ('um ponteiro para tabela que o suplementar nao tem',
     sub_um('sec_method.tex', 'Table~S17 states, for each of the sixteen operations',
            'Table~S91 states, for each of the sixteen operations')),
    ('o termo fora da convencao, de volta no resumo grafico',
     sub_um('graphical_abstract.tex',
            'Do visual-selection operations measure technical quality?',
            'What does the visual-quality criterion actually measure?')),
    # ⚠️ a versao anterior desta linha usava `\mchImplantada`, que renderiza um NUMERO:
    # a guarda so olha macro que renderiza palavra em minuscula, entao a mutacao nao
    # exercitava a classe dela. Aqui a macro rende «eleven».
    # ⭐ as duas guardas de 08/09 que nenhuma mutacao atacava ainda
    ('um comando LaTeX vazando como texto no PDF',
     sub_um('sec_method.tex', 'Table~S17 states, for each',
            'citetcakmak2025tripss Table~S17 states, for each')),
    ('uma linha passando da margem do suplementar',
     sub_um('supplementary.tex', '\\bibliography{references}',
            # ⚠️ a versao anterior usava `[l]`, que alinha o texto A ESQUERDA dentro da caixa
     # larga: a caixa e invisivel, entao nao havia TINTA alem da margem e a guarda,
     # que mede tinta, nao tinha o que ver. A mutacao e que estava errada.
     '\\noindent\\makebox[17cm][r]{estouro deliberado da margem}\n\n\\bibliography{references}')),
    # ⚠️ a guarda 28 (scripts rodam do clone) NAO da para atacar daqui: ela le o
    # REPOSITORIO num caminho absoluto, e a mutacao so mexe na copia da pasta do artigo.
    ('uma frase abrindo com macro em minuscula',
     sub_um('sec_method.tex', 'The audited set is \\fontesOperacoes{} operations',
            '\\fontesTrabalhos{} source works define the audited set of'
            ' \\fontesOperacoes{} operations')),
]


def roda(raiz):
    r = subprocess.run([PY_, 'verifica_tudo.py'], cwd=raiz, capture_output=True, text=True)
    saida = r.stdout + r.stderr
    reprovou = 'TUDO APROVA' not in saida
    quem = re.findall(r'REPROVOU: ([^\n]+)', saida) or re.findall(r'⛔ ([^\n]+)', saida)
    return reprovou, (quem[0][:76] if quem else '(sem linha de reprovacao)')


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    # ⛔ INSTANTANEO UNICO, tirado antes da primeira mutacao. Copiar a pasta viva a cada
    # iteracao contamina o placar: editando o artigo durante a rodada, «teto de paginas»
    # disparou em mutacoes que nao mexem em pagina nenhuma, porque a copia pegou um estado
    # intermediario. O instantaneo tambem torna a rodada reprodutivel.
    PRISTINO = TMP.parent / (TMP.name + '-pristino')
    if PRISTINO.exists():
        shutil.rmtree(PRISTINO)
    shutil.copytree(AQUI, PRISTINO, ignore=shutil.ignore_patterns(
        '__pycache__', '*.bak', 'mut*', '.cache_crossref.json'))
    c = AQUI / '.cache_crossref.json'          # senao a guarda de DOI sai por falta de rede
    if c.exists():
        shutil.copy(c, PRISTINO / c.name)
    base_reprova, base_quem = roda(PRISTINO)
    if base_reprova:
        print('  ⛔ o instantaneo SEM mutacao ja reprova (%s): o placar nao valeria nada'
              % base_quem)
        shutil.rmtree(PRISTINO)
        return 1
    pegas, reparadas, soltas = [], [], []
    for nome, (aplicar, ainda_esta_la) in MUTACOES:
        shutil.copytree(PRISTINO, TMP)
        try:
            aplicar(TMP)
            reprovou, quem = roda(TMP)
            # ⚠️ TERCEIRO desfecho, que nao e nem pega nem buraco: o pipeline REPAROU a
            # mutacao antes das guardas. O `sincroniza_ponteiros` reescreve a faixa
            # «S1--SN» do corpo a partir do .aux, entao a faixa desatualizada nunca chega
            # a ser julgada. Chamar isso de «escapou» seria acusar errado.
            reparada = not reprovou and not ainda_esta_la(TMP)
        finally:
            shutil.rmtree(TMP, ignore_errors=True)
        if reprovou:
            pegas.append(nome)
            print('  ✅ PEGA      %-44s %s' % (nome, quem))
        elif reparada:
            reparadas.append(nome)
            print('  🔧 REPARADA  %-44s (o pipeline desfez antes das guardas)' % nome)
        else:
            soltas.append(nome)
            print('  ⛔ ESCAPOU   %s' % nome)
    print('\n  %d pegas, %d reparadas pelo pipeline, %d escaparam, de %d'
          % (len(pegas), len(reparadas), len(soltas), len(MUTACOES)))
    for nome in soltas:
        print('    ⛔ buraco medido: %s' % nome)
    shutil.rmtree(PRISTINO, ignore_errors=True)
    return 0 if not soltas else 1


if __name__ == '__main__':
    sys.exit(main())
