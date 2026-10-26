#!/usr/bin/env python3
"""⛔ CADA CELULA DA TABELA DOS PARES CONSTRUIDOS BATE COM A FONTE?

POR QUE EXISTE (08/09/2026). A `tab:constructed` e a evidencia central do artigo — doze
metodos por oito degradacoes — e esta DIGITADA a mao dentro do `sec_results.tex`. O teste de
mutacao mostrou que decimal digitado passa por todas as guardas; esta tabela tem 108 numeros
digitados e nenhuma guarda olhava para eles. Um digito trocado ali compila, imprime e passa.

⭐ COMO SEPARA: cada linha vira a tupla das oito degradacoes MAIS a media, e essa tupla tem
de bater, celula a celula, com a linha correspondente do `TABELA_FINAL.json`. Nove numeros
por linha: o acaso nao ajuda, e a taxa base disso e medida no autoteste com sorteio.

⚠️ A media impressa e arredondada a uma casa e as celulas a zero: a comparacao respeita cada
formato, em vez de exigir igualdade exata de float.
"""
import io
import json
import math
import random
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
QB = Path('/data/projects/benchmark')
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']

# o nome impresso -> a chave da fonte
NOMES = {
    'SIFT+BoVW': 'SIFT+BoVW', 'LIQE': 'liqe', 'TOPIQ': 'topiq_nr',
    'MUSIQ': 'musiq', 'QualiCLIP': 'qualiclip', 'ARNIQA': 'arniqa', 'DBCNN': 'dbcnn',
    'NIQE': 'niqe', 'CLIP-IQA$+$': 'clipiqa_plus', 'HyperIQA': 'hyperiqa',
    'CLIP-IQA': 'clipiqa', 'BRISQUE': 'brisque',
}
# ⭐ 28/09 (cli-3, pedido do [author]): a ultima banda da tabela traz as tres proxies profundas da
# Tabela 3, cada uma do arquivo que a mediu. O centroide tem meias decisoes (15 de 800 pares
# cujo original esta em dois clusters que discordam), entao a celula pode terminar em ,5:
# a regra de arredondamento e MEIO PARA CIMA, declarada, e nao o `round` bancario do Python,
# que levaria 76,5 a 76 e 75,5 a 76 na mesma linha.
PROFUNDAS = {
    'Feature-vector norm': ('classe4_na_bancada_pareada.json', 'deep_norma'),
    'Frame coherence': ('classe4_na_bancada_pareada.json', 'deep_coerencia'),
    'Cluster-centre distance': ('classe4_centroide_na_bancada.json', None),
}


def _meio_para_cima(x, casas=0):
    f = 10 ** casas
    return math.floor(x * f + 0.5) / f


def _fonte_profunda(nome):
    arq, op = PROFUNDAS[nome]
    d = json.loads((QB / arq).read_text())
    r = d['por_operacao'][op] if op else d['primaria_centroide_com_todos_os_membros_mais_a_copia']
    return {'acc': dict(zip(r['ordem'], r['acuracia_por_tipo'])), 'media': r['media']}


def celulas(texto=None):
    """Le a tabela do corpo e devolve {nome impresso: [oito celulas, media]}."""
    t = texto if texto is not None else (AQUI / 'sec_results.tex').read_text(encoding='utf-8')
    i = t.index(r'\label{tab:constructed}')
    corpo = t[i:t.index(r'\end{tabular}', i)]
    corpo = corpo[corpo.index(r'\midrule'):]
    out = {}
    for linha in re.split(r'\\\\', corpo):
        linha = linha.replace('\\midrule', '').strip()
        if '&' not in linha:
            continue
        campos = [c.strip() for c in linha.split('&')]
        nome = re.sub(r'\\rowcolor\{[^}]*\}', '', campos[0]).strip()
        if nome not in NOMES and nome not in PROFUNDAS:
            continue
        vals = []
        for c in campos[1:]:
            m = re.findall(r'\d+\.?\d*', c)
            vals.append(float(m[-1]) if m else None)
        out[nome] = vals
    return out


def confere(texto=None):
    fonte = {l['nome']: l for l in json.loads((QB / 'TABELA_FINAL.json').read_text())['linhas']}
    tab = celulas(texto)
    ruins = []
    if len(tab) != len(NOMES) + len(PROFUNDAS):
        ruins.append('a tabela tem %d linhas reconhecidas e o mapa tem %d'
                     % (len(tab), len(NOMES) + len(PROFUNDAS)))
    n = 0
    for nome, vals in tab.items():
        f = _fonte_profunda(nome) if nome in PROFUNDAS else fonte.get(NOMES[nome])
        if f is None:
            ruins.append('%s: sem linha na fonte' % nome)
            continue
        if len(vals) != 9:
            ruins.append('%s: %d colunas, esperava 9' % (nome, len(vals)))
            continue
        for t_, v in zip(TIPOS, vals[:8]):
            n += 1
            if v is None or abs(v - _meio_para_cima(f['acc'][t_])) > 1e-9:
                ruins.append('%s/%s: a tabela diz %s e a fonte %s' % (nome, t_, v, f['acc'][t_]))
        n += 1
        if vals[8] is None or abs(vals[8] - _meio_para_cima(f['media'], 1)) > 1e-9:
            ruins.append('%s/media: a tabela diz %s e a fonte %.1f' % (nome, vals[8], f['media']))
    return not ruins, ruins, n


def _taxa_base():
    """⚠️ Uma checagem que um sorteio passa nao vale nada. Aqui o sorteio troca UMA celula
    por um inteiro qualquer de 0 a 100 e a guarda tem de reprovar quase sempre."""
    t = (AQUI / 'sec_results.tex').read_text(encoding='utf-8')
    r = random.Random(42)
    passou = 0
    for _ in range(200):
        m = list(re.finditer(r'(?m)^(TOPIQ|MUSIQ|DBCNN|BRISQUE) & (\d+)', t))
        alvo = m[r.randrange(len(m))]
        novo = t[:alvo.start(2)] + str(r.randint(0, 100)) + t[alvo.end(2):]
        if confere(novo)[0]:
            passou += 1
    return passou / 200


def autoteste():
    ok, ruins, _ = confere()
    if not ok:
        print('    ⛔ autoteste: a tabela corrente ja nao bate: %s' % ruins[:2])
        return False
    # ⛔ o defeito real que motivou a familia: um digito trocado
    doente = (AQUI / 'sec_results.tex').read_text(encoding='utf-8').replace(
        'TOPIQ & 93 & 100', 'TOPIQ & 39 & 100', 1)
    if confere(doente)[0]:
        print('    ⛔ autoteste: aprovou a tabela com um digito trocado')
        return False
    # e na banda nova, a do centroide
    doente3 = (AQUI / 'sec_results.tex').read_text(encoding='utf-8').replace(
        'Cluster-centre distance & 56', 'Cluster-centre distance & 65', 1)
    if confere(doente3)[0]:
        print('    ⛔ autoteste: aprovou a linha do centroide com um digito trocado')
        return False
    # e a media, que e o numero que o leitor compara entre linhas
    doente2 = (AQUI / 'sec_results.tex').read_text(encoding='utf-8').replace(
        '& \\textbf{99.5} \\\\', '& \\textbf{95.5} \\\\', 1)
    if confere(doente2)[0]:
        print('    ⛔ autoteste: aprovou a tabela com a media trocada')
        return False
    tb = _taxa_base()
    if tb > .02:
        print('    ⛔ autoteste: taxa base de %.1f %%, a checagem nao discrimina' % (100 * tb))
        return False
    print('   autoteste ✅ (reprova digito e media trocados; taxa base %.1f %%)' % (100 * tb))
    return True


if __name__ == '__main__':
    if not autoteste():
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d celulas da tabela dos pares construidos conferidas contra a fonte' % n)
    for x in ruins[:8]:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
