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
QB = Path('/dados/Projetos/quality-benchmark')
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
    jus = {x['nome']: x for x in
           json.load(open(QB / 'jusante_lado_a_lado.json'))['linhas']
           if 'sumarizacao' in x['familia']}

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
    ko = json.load(open(QB / 'o_modulo_do_korolkov_nos_11_segmentos.json'))
    out['__KOROLKOV__'] = _mod(ko['modulo_por_tipo'])
    # ⚠️ o membro que aparece no bloco do modulo e o medido nos MESMOS 11 segmentos
    out['__KOROLKOV_SHARP__'] = _mod(ko['membros']['laplacian_var']['por_tipo'])
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
        if len(c) != 12:
            continue

        oito = tuple(_num(x) for x in c[1:9])
        if any(v is None for v in oito):
            continue
        med = _num(c[9])
        ag = None if 'n/a' in c[10] else _num(c[10])
        kp = None if 'n/a' in c[11] else _num(c[11])
        linhas.append((oito, med, ag, kp))
    return linhas


def confere(texto=None):
    esp = set()
    for oito, med, ag, kp in esperado().values():
        esp.add((oito, med,
                 None if ag is None else round(ag, 3),
                 None if kp is None else round(kp, 1)))
    faltas = []
    li = lidas(texto)
    for t in li:
        alvo = (t[0], t[1],
                None if t[2] is None else round(t[2], 3),
                None if t[3] is None else round(t[3], 1))
        if alvo not in esp:
            faltas.append('linha sem fonte identica: %s' % (alvo,))
    return not faltas, faltas, len(li)


def _taxa_base():
    """Uma linha ALEATORIA passaria? Mede antes de confiar na guarda."""
    rnd = random.Random(42)
    esp = confere()  # so para carregar
    passou = 0
    for _ in range(200):
        falsa = (tuple(float(rnd.randrange(0, 101)) for _ in range(8)),
                 round(rnd.uniform(0, 100), 1), None, None)
        ok, _f, _n = confere(_linha_falsa(falsa))
        passou += ok
    return passou / 200.0


def _linha_falsa(t):
    oito = ' & '.join(r'\cellcolor{perf3!80}%g' % v for v in t[0])
    return ('X & %s & \\textbf{%.1f} & \\textcolor{black!30}{\\tiny n/a} & '
            '\\textcolor{black!30}{\\tiny n/a}\\\\' % (oito, t[1]))


def _autoteste():
    """⭐ Duas pernas: o estado atual passa, e o zero comido REPROVA de verdade."""
    ok, f, n = confere()
    assert ok, '⛔ celula sem fonte: %s' % f
    assert n == 19, '⛔ li %d linhas de componente, esperava 19' % n
    orig = TEX.read_text(encoding='utf-8')
    sujo = orig.replace(r'\textbf{40.5}', r'\textbf{4.5}', 1)
    if sujo == orig:                       # o 40.5 mora na tabela do jusante
        sujo = orig.replace(r'\textbf{83.1}', r'\textbf{8.31}', 1)
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
