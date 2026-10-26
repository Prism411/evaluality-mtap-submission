#!/usr/bin/env python3
"""⛔ CADA CELULA DA TABELA DE SINTESE BATE COM A FONTE DAQUELA COLUNA?

POR QUE EXISTE (07/09/2026). A tabela imprimiu **4.5** onde o dado e **40.5**: o
`.replace('0.', '.')` que tira o zero a esquerda comeu o zero INTERNO. O LaTeX compilou,
nenhuma guarda reclamou, e so apareceu quando eu OLHEI a pagina renderizada.

⚠️ E A PRIMEIRA VERSAO DESTA GUARDA NAO SEPARAVA NADA. Ela procurava o numero impresso em
qualquer lugar da uniao dos JSONs de origem, e essa uniao tem 2689 valores distintos de uma
casa: um numero ALEATORIO em [0,100] passava em **65 % das vezes**. Alimentada com o
defeito, ela APROVOU. Taxa base medida antes de confiar, como manda a casa.

⛔ E EM 08/09 ELA FALHOU DE OUTRO JEITO, pior: continuou dizendo ✅ conferindo a
`tab_cadeia.tex` DEPOIS que essa tabela saiu do artigo. Guarda que le a fonte errada aprova
o mundo errado. Agora ela le a `tab_sintese.tex`, que e a que o corpo imprime.

⭐ COMO SEPARA: cada linha vira a tupla completa das oito degradacoes + media + concordancia
+ jusante, e essa tupla precisa existir, IDENTICA, em alguma operacao da fonte. Com onze
casas o acaso nao ajuda, e a taxa base disso e medida no autoteste.
"""
import json
import random
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
QB = Path('/data/projects/benchmark')
TEX = AQUI / 'tab_sintese.tex'
TIPOS = ["dark", "motion", "blur", "h264", "rescale", "satur", "noise", "jpeg"]


def esperado():
    """operacao -> (oito acuracias, media, kappa, jusante), cada uma da sua fonte."""
    designA = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
    apur = json.load(open(QB / 'apuracao_ops.json'))
    alinha = apur['pares_alinhados_por_construcao']
    piso = {x['operacao']: x for x in
            json.load(open(QB / 'o_piso_das_operacoes_isoladas_e_estavel.json'))['por_operacao']}
    # ⛔ SO o lado de sumarizacao: o lado NR-IQA deste arquivo mede contra o Q-Align e nao
    # contra o SIFT implantado, e esta marcado _INUTILIZAVEL na propria fonte.
    # ⚠️ 22/09 (parecer v4, 2.5): a coluna de retencao da Tabela 6 passou a ler tambem o
    #    caminho publicado, porque marcar «n/a» onde a Figura S4 mostra um numero fazia as
    #    duas pecas discordarem sobre a mesma celula. A guarda le a MESMA uniao, senao ela
    #    reprova a correcao em vez do defeito.
    jus = {n: {'nome': n, 'pct': v['pct']} for n, v in json.load(open(
        QB / 'jusante_ops_faltantes_caminho_velho.json'))['concordancia_com_sift'].items()}
    jus.update({x['nome']: x for x in
           json.load(open(QB / 'jusante_lado_a_lado.json'))['linhas']
           if 'sumarizacao' in x['familia']})

    out = {}
    for op, v in designA.items():
        m = dict(zip(v['ordem'], v['acuracia_por_tipo']))
        if any(m.get(t) is None for t in TIPOS):
            continue
        # ⛔ a media e sobre as OITO, igual em todas as linhas: e o que torna a coluna
        # comparavel entre operacoes. A regua «fora os alinhados» vive no suplementar.
        vals = [m[t] for t in TIPOS]
        out[op] = (tuple(float(round(m[t])) for t in TIPOS), round(sum(vals) / len(vals), 1),
                   piso.get(op, {}).get('kappa'), jus.get(op, {}).get('pct'))

    # os dois modulos vem do arquivo que os mediu
    def _mod(pt):
        return (tuple(float(round(pt[t])) for t in TIPOS),
                round(sum(pt[t] for t in TIPOS) / len(TIPOS), 1), None, None)

    va = json.load(open(QB / 'o_vascore_do_qaroush_como_a_Eq20_manda.json'))
    out['__VASCORE__'] = _mod(va['modulo']['VAScore_soma_crua_Eq20']['por_tipo'])
    # ⭐ 27/09 (cli-3): a banda do Qaroush passou a mostrar os cinco termos da Eq. 20; o MMI
    # sai do mesmo arquivo do modulo, nao do designA.
    out['__VA_MMI__'] = _mod(va['membros']['qaroush_mmi']['por_tipo'])
    ko = json.load(open(QB / 'o_modulo_do_korolkov_nos_11_segmentos.json'))
    out['__KOROLKOV__'] = _mod(ko['modulo_por_tipo'])
    # ⚠️ o membro que aparece no bloco do modulo e o medido nos MESMOS 11 segmentos
    out['__KOROLKOV_SHARP__'] = _mod(ko['membros']['laplacian_var']['por_tipo'])
    # ⭐ 27/09 (parecer, C): as duas linhas novas da Tabela 6. Elas NAO estao no
    # designA -- nao sao operacoes da varredura --, entao a degradacao vem da
    # TABELA_FINAL, medida nos mesmos 800 pares e nos mesmos oito tipos.
    _tf = {l['nome']: l for l in json.load(open(QB / 'TABELA_FINAL.json'))['linhas']}
    _sub = json.load(open(QB / 'a_substituicao_concorda_acima_do_acaso.json'))
    _sift = _mod(_tf['SIFT+BoVW']['acc'])
    # ⚠️ o Agr do SIFT+BoVW e contra o LIQE, o mesmo regime da coluna. O do
    # BRISQUE fica None: contra o LIQE ele nao foi medido, e o unico numero que
    # existe para ele e contra o Q-Align, noutro regime.
    out['__SIFTBOVW__'] = (_sift[0], _sift[1],
                           _sub['por_linha']['liqe_x_implantada']['kappa_contra_o_acaso'],
                           None)
    # ⭐ o Agr do BRISQUE vem de `piso_as_duas_familias.json`, a fonte da
    # afirmacao de referencia comum da 4.5 -- NAO do arquivo de estabilidade,
    # que so tem operacoes. A guarda le a mesma fonte que o gerador.
    _bq = _mod(_tf['brisque']['acc'])
    _duas = json.load(open(QB / 'piso_as_duas_familias.json'))['por_metodo']['brisque']
    assert _duas['n_clusters'] == 42, '⛔ o BRISQUE mudou de populacao'
    out['__BRISQUE__'] = (_bq[0], _bq[1], _duas['kappa_uniform'], None)
    return out


# ⚠️ DUAS ARMADILHAS numa celula como `\cellcolor{perf5!45}100`:
#   1. `perf5!45` tem digitos, e um regex ingenuo devolve 5 em vez de 100;
#   2. o artigo suprime o zero a esquerda, entao `$+.416$` vale 0,416 e nao 416.
# Por isso os involucros saem PRIMEIRO, com o conteudo das chaves, e so depois o numero.
INVOLUCRO = re.compile(r'\\(?:cell|text)color\{[^}]*\}|\\[a-zA-Z]+')
NUMERO = re.compile(r'([+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+))')


def _num(x):
    y = INVOLUCRO.sub(' ', x)
    y = y.replace('{', ' ').replace('}', ' ').replace('$', ' ')
    m = NUMERO.search(y)
    return None if m is None else float(m.group(1))


def lidas(texto=None):
    """Cada linha de componente do .tex vira a mesma tupla."""
    s = texto if texto is not None else TEX.read_text(encoding='utf-8')
    linhas = []
    for l in s.split('\n'):
        if 'multicolumn' in l or '&' not in l or 'textbf{Mean}' in l:
            continue
        c = [x.strip() for x in l.split('&')]
        if len(c) != 11:
            continue

        oito = tuple(_num(x) for x in c[1:9])
        if any(v is None for v in oito):
            continue
        med = _num(c[9])
        ag = None if 'n/a' in c[10] else _num(c[10])
        linhas.append((oito, med, ag, None))
    return linhas


# ⛔ TOLERANCIA DE MEIA UNIDADE NA ULTIMA CASA, e nao igualdade de dois
# arredondamentos independentes.
#
# POR QUE (21/09/2026, achado do `@agente-iqa-cli-2` e adotado aqui). Comparar
# `round(x, k)` do lado da fonte com o numero impresso supoe que os DOIS lados arredondem
# igual. Eles nem sempre arredondam: o `round()` do Python e meio-para-par
# (`round(2.5)` da 2 e `round(0.5)` da 0), e quem formata por outro caminho, ou quem
# escreve a mao, produz meio-para-cima. Nesta implementacao os dois coincidem, porque os
# dois lados saem de Python, MAS a igualdade exata entre arredondamentos independentes e
# fragil de proposito errado: ela quebra quando o gerador troca de rota de formatacao, e
# quebrar ali seria alarme falso, nao defeito.
#
# ⭐ O criterio robusto e: o valor da fonte tem de estar a MENOS DE MEIA UNIDADE da ultima
# casa impressa. Com uma casa, tolerancia 0,05; com tres, 0,0005. Isso aceita qualquer
# convencao de arredondamento e continua reprovando o defeito que esta guarda existe para
# pegar, que e de ordem de grandeza (o 40.5 impresso como 4.5 erra por 36).
def _perto(a, b, casas):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= 0.5 * (10 ** -casas) + 1e-12


def confere(texto=None):
    esp = list(esperado().values())
    faltas = []
    li = lidas(texto)
    for t in li:
        achou = False
        for oito, med, ag, kp in esp:
            if (len(t[0]) == len(oito)
                    and all(_perto(x, y, 0) for x, y in zip(t[0], oito))
                    and _perto(t[1], med, 1)
                    and _perto(t[2], ag, 3)):
                achou = True
                break
        if not achou:
            faltas.append('linha sem fonte dentro da tolerancia: %s' % (t,))
    return not faltas, faltas, len(li)


def _taxa_base():
    """Uma linha ALEATORIA passaria? Mede antes de confiar na guarda."""
    rnd = random.Random(42)
    esp = confere()  # so para carregar
    _n0 = len(lidas())
    _teste = _linha_falsa((tuple(1.0 for _ in range(8)), 1.0))
    assert len(lidas(TEX.read_text(encoding='utf-8') + '\n' + _teste)) == _n0 + 1, (
        '⛔ a linha falsa nao e LIDA pelo parser: a taxa base mediria o vazio')
    passou = 0
    for _ in range(200):
        falsa = (tuple(float(rnd.randrange(0, 101)) for _ in range(8)),
                 round(rnd.uniform(0, 100), 1), None, None)
        ok, _f, _n = confere(_linha_falsa(falsa))
        passou += ok
    return passou / 200.0


def _linha_falsa(t):
    """Uma linha de componente PLAUSIVEL, para medir a taxa base.

    ⛔ 27/09: esta funcao montava DOZE campos e o `lidas()` so aceita ONZE --
    sobra de quando a tabela ainda tinha a coluna `Kp`. A linha falsa era
    descartada antes de ser conferida, entao a taxa base media o vazio e
    imprimia «100 %» ao lado de um ✅. Controle que nao entra no mundo nao e
    controle; o assert abaixo garante que ele entra.
    """
    oito = ' & '.join(r'\cellcolor{perf3!80}%g' % v for v in t[0])
    return ('X & %s & \\textbf{%.1f} & \\textcolor{black!30}{\\tiny n/a}\\\\'
            % (oito, t[1]))


def _autoteste():
    """⭐ Duas pernas: o estado atual passa, e o zero comido REPROVA de verdade."""
    ok, f, n = confere()
    assert ok, '⛔ celula sem fonte: %s' % f
    # 25/09: +1 com a banda do Xu. 27/09 (parecer, C): +2, o BRISQUE da banda
    # do Xu e a banda do SIFT+BoVW. O numero fica DECLARADO: se uma linha
    # sumir da tabela, esta guarda reprova em vez de conferir menos celulas.
    # ⚠️ 27/09 (cli-3): 22 -> 24, as linhas CF (colourfulness) e MMI da banda do Qaroush.
    assert n == 24, '⛔ li %d linhas de componente, esperava 24' % n
    orig = TEX.read_text(encoding='utf-8')
    sujo = orig.replace(r'\textbf{83.8}', r'\textbf{8.38}', 1)
    assert sujo != orig, '⛔ nao consegui montar o mundo errado'
    assert not confere(sujo)[0], '⛔ NAO separa: o zero comido passou'
    return True


if __name__ == '__main__':
    assert _autoteste()
    tb = _taxa_base()
    ok, faltas, n = confere()
    print('  autoteste ✅ (com o zero comido a guarda REPROVA)')
    print('  taxa base: linha aleatoria passa em %.1f %% das vezes' % (100 * tb))
    print('  %d linhas x 11 colunas conferidas contra a fonte de cada uma' % n)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    for x in faltas:
        print('    %s' % x)
    sys.exit(0 if ok else 1)
