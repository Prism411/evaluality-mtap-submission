#!/usr/bin/env python3
r"""⛔ «VER A SECAO X» QUANDO A SECAO X JA NAO DIZ AQUILO.

POR QUE EXISTE (14/09/2026). Numa consolidacao editorial eu apaguei, da §3.1, a frase que
dizia qual mapa de saliencia foi usado — o residuo espectral de Hou e Zhang. O resultado
(§4.3) continuou escrito «whose saliency input is the adaptation of Section~3.1». O ponteiro
ficou apontando para uma especificacao que nao existia mais, e **`spectral-residual` sobrou
so no `references.bib`**: nenhum `.tex` do pacote dizia mais QUAL metodo foi avaliado.

🔴 Nada quebrou. O LaTeX compilou, a `\ref` resolveu para uma secao que existe, as 37
guardas aprovaram. ⚠️ **Este e o modo de falha da edicao por corte**: a guarda de ponteiros
confere que o ALVO existe, nunca que o alvo ainda CONTEM o que a frase promete. Quem achou
foi um leitor humano.

⭐ A regra: cada remissao declarada aqui liga a frase que promete ao termo que a secao-alvo
tem de conter. Se o termo sumir, isto REPROVA e diz qual frase ficou orfa. A lista cresce
quando uma remissao nova aparecer; uma remissao sem entrada nao e erro, e uma nao coberta.
"""
import re, sys
from pathlib import Path

A = Path(__file__).parent
CORPO = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# (trecho que promete, rotulo para onde ele manda, termo que o alvo tem de conter)
# ⛔ 21/09, depois do corte do corpo: as quatro entradas apontavam para frases que a
# reescrita substituiu, e a guarda acusou as quatro. Cada uma foi reapontada para a frase
# ATUAL que faz a mesma promessa; a do `saliency input` SAIU, porque aquela remissao nao
# existe mais no corpo e entrada morta reprova em vez de ficar de reserva.
REMISSOES = [
    ('Section~\\ref{sec:mechanism} measures the chain end to end', 'sec:mechanism',
     r'descriptor count'),
    # ⚠️ 21/09: a frase virou «the evidence on validity is the screening of».
    # ⚠️ 22/09 (parecer v5, §3): a abertura da 4.6 perdeu a sequencia de negacoes, e a
    #    remissao passou a viver na frase que diz QUAL pergunta a triagem responde.
    # ⚠️ 22/09 (parecer v6, 2.1): a frase atribuia a triagem a escolha da MELHOR
    #    selecao, que o desenho dela nao produz. Agora ela diz o que a triagem faz.
    # ⛔ 27/09 (cli-3): a remissao para sec:screen saiu da 4.6 junto com a frase (exemplo
    #    literal do parecer do [author]). Entrada morta sai, nao fica de reserva.
    # ⭐ 21/09: a legenda da figura de escopo deixou de desenhar o pipeline implantado e
    # passou a mandar o aparato para uma secao. Esse ponteiro e a unica coisa que impede a
    # figura de ficar sem dizer QUAL pipeline forneceu os segmentos, e ele vai mudar de
    # alvo quando a subsecao de aparato existir. Declarado aqui para nao envelhecer calado.
    # ⚠️ 21/09, mais tarde: a legenda foi reescrita por FG01 («any pipeline would serve»
    # saiu), e esta entrada ficou apontando para uma frase que nao existe mais. A guarda
    # acusou — que e exatamente para o que ela serve. Trecho atualizado, alvo o mesmo.
    # ⚠️ 27/09 (cli-3): legenda encurtada; o ponteiro para sec:data ficou.
    ('All other pipeline stages are held fixed', 'sec:data',
     r'redundancy stage produced by|multi-member clusters'),
]


def _texto():
    return {n: (A / n).read_text(encoding='utf-8', errors='replace')
            for n in CORPO if (A / n).exists()}


def _corpo_da_secao(rotulo, docs):
    """O texto entre \\label{rotulo} e o proximo \\section ou \\subsection."""
    for t in docs.values():
        i = t.find('\\label{%s}' % rotulo)
        if i < 0:
            continue
        j = min([x for x in (t.find('\n\\subsection', i + 1), t.find('\n\\section', i + 1))
                 if x > 0] or [len(t)])
        return t[i:j]
    return None


def orfas(docs=None):
    docs = _texto() if docs is None else docs
    ruins, mortas = [], []
    for promessa, rotulo, termo in REMISSOES:
        # a frase que promete tolera quebra de linha
        pat = re.compile(r'\s+'.join(re.escape(w) for w in promessa.split()))
        onde = [n for n, t in docs.items() if pat.search(t)]
        if not onde:
            mortas.append(promessa[:46])   # declarada e sem casar: parou de conferir
            continue
        alvo = _corpo_da_secao(rotulo, docs)
        if alvo is None:
            ruins.append((promessa[:46], rotulo, 'o rotulo nao existe em lugar nenhum'))
        elif not re.search(termo, alvo, re.I):
            ruins.append((promessa[:46], rotulo,
                          'a secao nao contem mais «%s»' % termo))
    for m in mortas:
        ruins.append((m, '-', 'entrada declarada que nao casa frase nenhuma: '
                              'atualize o trecho ou remova a entrada'))
    return ruins


def main():
    r = orfas()
    if r:
        print(f'  ⛔ {len(r)} remissao(oes) apontam para o que a secao ja nao diz:')
        for p_, rot, por in r:
            print(f'       «{p_}...» -> {rot}: {por}')
        return 1
    print(f'  ✅ as {len(REMISSOES)} remissoes declaradas acham o que prometem')
    return 0


def autoteste():
    """Duas pernas: o corpo atual passa, e apagar a especificacao REPROVA."""
    docs = _texto()
    mal = 0
    n = len(orfas(docs))
    print(f"  {'✅' if n == 0 else '⛔'} o corpo atual: {n} orfa(s), esperado 0")
    mal += n != 0
    # ⛔ o defeito real de 14/09, replantado: some a especificacao, fica o ponteiro
    doente = dict(docs)
    doente['sec_method.tex'] = re.sub(
        r'Saliency area was computed from a spectral-residual map[^.]*\.', '',
        doente['sec_method.tex'])
    n = len(orfas(doente))
    print(f"  {'✅' if n == 1 else '⛔'} sem a frase da saliencia: {n} orfa(s), esperado 1")
    mal += n != 1
    # ⚠️ e a perna que separa: se a PROMESSA sair do corpo e a entrada ficar aqui, ela
    #    para de conferir em silencio. Isso tambem tem de REPROVAR, senao a guarda
    #    envelhece junto com o texto, que foi exatamente o buraco de 14/09 pela manha.
    sem = dict(docs)
    sem['sec_results.tex'] = sem['sec_results.tex'].replace(
        'Section~\\ref{sec:mechanism} measures the chain end to end', 'computed as')
    n = len(orfas(sem))
    print(f"  {'✅' if n == 1 else '⛔'} entrada declarada sem frase no corpo: {n}, esperado 1")
    mal += n != 1
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
