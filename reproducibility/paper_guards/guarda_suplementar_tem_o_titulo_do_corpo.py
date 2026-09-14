#!/usr/bin/env python3
"""⛔ O SUPLEMENTAR CARREGA O TITULO ATUAL DO ARTIGO?

POR QUE EXISTE (12/09/2026). O corpo foi renomeado e o suplementar ficou para tras: ele
anunciava «A Component-Level Audit of No-Reference Quality Scoring in a Multi-Video
Summarization Pipeline» enquanto o artigo ja se chamava outra coisa. Nada reprovava,
porque sao dois documentos e nenhum \\ref liga um ao outro — o titulo e DIGITADO duas
vezes. Um revisor achou; nenhuma das 31 guardas achava.

⚠️ E o custo e alto: a Springer publica o material suplementar COMO RECEBIDO, sem passar
por edicao. Um titulo velho vai impresso.

Autoteste de duas pernas: o estado certo passa, e o titulo antigo REPROVA nominalmente.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent


def titulo_do_corpo(texto=None):
    t = texto if texto is not None else (AQUI / 'main.tex').read_text(encoding='utf-8')
    m = re.search(r'\\title\[[^\]]*\]\{(.+?)\}\s*\n', t, re.S)
    assert m, '⛔ nao achei \\title{...} em main.tex'
    return ' '.join(m.group(1).split())


def titulo_no_suplementar(texto=None):
    t = texto if texto is not None else (AQUI / 'supplementary.tex').read_text(encoding='utf-8')
    m = re.search(r'\\title\[[^\]]*\]\{(.+?)\}\s*\n', t, re.S)
    assert m, '⛔ nao achei \\title{...} em supplementary.tex'
    return ' '.join(m.group(1).split())


def confere(corpo=None, supl=None):
    alvo, tem = titulo_do_corpo(corpo), titulo_no_suplementar(supl)
    return alvo in tem, alvo, tem


def nomeia_o_periodico(texto=None):
    t = texto if texto is not None else (AQUI / 'supplementary.tex').read_text(encoding='utf-8')
    return 'Multimedia Tools and Applications' in t


def _autoteste():
    ok, alvo, _ = confere()
    assert ok, '⛔ o estado atual deveria passar'
    velho = ('\\title[Supplementary material]{Electronic Supplementary Material for\n'
             "``A Component-Level Audit of No-Reference Quality Scoring''}\n")
    mau, _, _ = confere(supl=velho)
    assert not mau, '⛔ NAO separa: o titulo antigo passou'
    # e nao pode aprovar por vacuo: um suplementar sem titulo tem de estourar, nao passar
    try:
        confere(supl='sem titulo nenhum\n')
        raise AssertionError('⛔ aprovou um suplementar sem titulo')
    except AssertionError as e:
        assert 'nao achei' in str(e), e
    print('  autoteste ✅ (o titulo antigo REPROVA; suplementar sem titulo estoura)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, alvo, tem = confere()
    per = nomeia_o_periodico()
    print('  corpo:       %s' % alvo[:78])
    print('  suplementar: %s' % tem[:78])
    print('  %s o suplementar carrega o titulo do corpo' % ('✅' if ok else '⛔'))
    print('  %s o suplementar nomeia o periodico' % ('✅' if per else '⛔'))
    sys.exit(0 if (ok and per) else 1)
