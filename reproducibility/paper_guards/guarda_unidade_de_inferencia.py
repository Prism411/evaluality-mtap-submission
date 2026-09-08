#!/usr/bin/env python3
"""⛔ O INTERVALO PUBLICADO FOI CALCULADO NA UNIDADE QUE O ROTULO DIZ?

POR QUE EXISTE (07-08/09/2026). A manchete imprimia «segment-block 95 % CI [+31,1, +37,7]».
O rotulo e prosa, o intervalo e numero, e nada no artigo os ligava. Recomputados os dois
esquemas, o intervalo publicado batia com a reamostragem POR PAR em 16 de 40 sementes e com
o bloco de segmento em 0 de 40: ele tratava 800 pares vindos de 20 segmentos como 800
observacoes independentes, e por isso saia mais ESTREITO (6,60 contra 9,13 pontos).

⭐ O sinal sobrevive — o limite inferior fica bem acima de zero nos dois esquemas — mas a
largura e o rotulo estavam errados, e isso e o tipo de defeito que nenhuma outra guarda
daqui pega: a aritmetica fecha, o LaTeX compila, e o numero e plausivel.

⚠️ E o teste so separa com o CONTROLE DA RIVAL. Exigir que a unidade declarada reproduza o
intervalo nao basta: duas unidades que acertem as duas nao dizem qual foi usada. O criterio
e «a declarada acerta E a rival erra», e e assim que os quatro eixos foram varridos em
`as_quatro_unidades_declaradas.json`.
"""
import io
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
FONTE = Path('/dados/Projetos/quality-benchmark/as_quatro_unidades_declaradas.json')

# ⚠️ o eixo que ERROU e foi corrigido: o corpo tem de imprimir o valor da unidade
# declarada, e nao pode mais imprimir o antigo.
EIXO_DA_MANCHETE = 'diferenca pareada, 800 pares'


def texto():
    return '\n'.join(f.read_text(encoding='utf-8') for f in sorted(AQUI.glob('sec_*.tex')))


def ic_impresso(t, a, b):
    """O intervalo como o corpo o escreve, tolerando espaco e o sinal explicito."""
    p = r'\$\[\s*\+?%s\s*,\s*\+?%s\s*\]\$' % (re.escape('%.1f' % a), re.escape('%.1f' % b))
    return re.search(p, t) is not None


def confere(t=None):
    t = texto() if t is None else t
    d = json.loads(FONTE.read_text(encoding='utf-8'))
    ruins = []
    for eixo, e in d['por_eixo'].items():
        # a classe inteira: a unidade declarada acerta e a rival erra
        if eixo == EIXO_DA_MANCHETE:
            a, b = e['publicado_agora']
            velho_a, velho_b = e['publicado_antes']
            if not ic_impresso(t, a, b):
                ruins.append('a manchete nao imprime o IC da unidade declarada '
                             '[+%.1f, +%.1f]' % (a, b))
            if ic_impresso(t, velho_a, velho_b):
                ruins.append('a manchete voltou a imprimir o IC por par '
                             '[+%.1f, +%.1f], rotulado como bloco de segmento'
                             % (velho_a, velho_b))
            continue
        if not e.get('reproduz_sob_a_declarada'):
            ruins.append('%s: o intervalo publicado NAO reproduz sob «%s», a unidade que o '
                         'rotulo declara' % (eixo, e['unidade_declarada']))
        if e.get('reproduz_sob_a_rival'):
            ruins.append('%s: reproduz tambem sob «%s», entao o rotulo nao esta preso ao '
                         'numero' % (eixo, e['rival']))
    return not ruins, ruins, len(d['por_eixo'])


def autoteste():
    """As duas pernas: aprovar o corpo certo e REPROVAR o corpo com o intervalo antigo."""
    falhas = []
    ok, _, _ = confere()
    if not ok:
        falhas.append('reprovou o corpo corrente (ver acima)')
    # ⛔ o defeito real de 07/09, replantado
    d = json.loads(FONTE.read_text(encoding='utf-8'))['por_eixo'][EIXO_DA_MANCHETE]
    a, b = d['publicado_agora']
    va, vb = d['publicado_antes']
    doente = texto().replace('$[+%.1f,+%.1f]$' % (a, b), '$[+%.1f,+%.1f]$' % (va, vb))
    ok2, _, _ = confere(doente)
    if ok2:
        falhas.append('aprovou o corpo com o IC por par de volta')
    # ⚠️ a perna acima passa NOS DOIS MUNDOS: como ela troca um intervalo pelo outro, a
    # checagem do valor NOVO ja basta para reprovar, e a do valor ANTIGO nunca e exercitada.
    # O caso que separa as duas e o antigo SOBREVIVENDO ao lado do novo — que e como o
    # defeito de fato reaparece, numa segunda frase que ninguem atualizou.
    ok4, _, _ = confere(texto() + '\n\nsegment-block 95\\%% CI $[+%.1f,+%.1f]$.' % (va, vb))
    if ok4:
        falhas.append('aprovou o corpo com o IC por par sobrevivendo ao lado do novo')
    # e a perna do sumico: se a frase perder o intervalo, tambem tem de reprovar
    ok3, _, _ = confere(texto().replace('$[+%.1f,+%.1f]$' % (a, b), ''))
    if ok3:
        falhas.append('aprovou o corpo sem intervalo nenhum')
    for f in falhas:
        print('    ⛔ autoteste: %s' % f)
    return not falhas


if __name__ == '__main__':
    if not FONTE.exists():
        print('  ⏳ a varredura das unidades nao esta em disco: nao aprova nem reprova')
        sys.exit(3)
    if not autoteste():
        print('  ⛔ REPROVA (a propria guarda nao separa)')
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d eixos com unidade de reamostragem declarada, conferidos contra a varredura' % n)
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
