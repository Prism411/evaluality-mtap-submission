#!/usr/bin/env python3
"""⭐⭐ O TIPO DE EVIDENCIA QUE A FONTE APRESENTA PREVE COMO A OPERACAO FALHA?

POR QUE EXISTE (08/09/2026). A tese do artigo liga PROVENIENCIA a COMPORTAMENTO. Ate aqui os
dois lados foram medidos separados: o que cada fonte valida, de um lado, e em quantos tipos
de degradacao cada operacao inverte, do outro. Ninguem tinha cruzado os dois.

A pergunta e direta: as operacoes que vem de fontes que validaram a PROPRIEDADE contra
julgamento humano invertem menos que as que vem de fontes que so avaliaram o RESUMO?

⚠️ O n e pequeno e o desenho e observacional: isto e uma DESCRICAO com teste declarado, nao
uma inferencia causal. O resultado entra no artigo so se separar; se nao separar, o registro
de que NAO separa tambem vale, e evita que alguem afirme a associacao sem medir.

PREVISOES, antes de rodar:
  1. as duas familias de evidencia tem n suficiente para um Mann-Whitney (>= 3 de cada lado)
  2. (hipotese) fontes que validam a propriedade invertem em MENOS tipos
"""
import json
from itertools import combinations
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')

# ⚠️ RODANDO DO PACOTE DE REPLICACAO: os arquivos que este script le sao os mesmos, mas
# ficam em `reproducibility/derived_data/`. Sem esta resolucao o pacote traz um script que
# so roda na maquina do autor, e a promessa de replicacao fica sem lastro.
def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent,
                 # ⚠️ na maquina do autor os dois arquivos de reanalise moram na pasta do
                 # artigo e o `synth_sift.json` no pacote; no clone todos estao em
                 # `derived_data`, que ja e a segunda opcao acima.
                 Path('/home/jader/memoria-agentes/07-Artigos/evaluality-literatura'),
                 Path('/dados/Projetos/evaluality-mtap-submission/reproducibility/derived_data')):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)

# ⚠️ rodando do pacote, QB nao existe: a saida vai para o lado do script
SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / 'a_evidencia_da_fonte_preve_a_falha.json'

VALIDA_A_PROPRIEDADE = 'julgamento humano da propriedade'


def mannwhitney_exato(a, b):
    """U e p bilateral por enumeracao: com n pequeno o exato e o certo."""
    n1, n2 = len(a), len(b)
    u = sum(1 for x in a for y in b if x > y) + .5 * sum(1 for x in a for y in b if x == y)
    todos = a + b
    piores = iguais = total = 0
    for comb in combinations(range(n1 + n2), n1):
        ga = [todos[i] for i in comb]
        gb = [todos[i] for i in range(n1 + n2) if i not in comb]
        uu = sum(1 for x in ga for y in gb if x > y) + .5 * sum(1 for x in ga for y in gb if x == y)
        total += 1
        d0, d = abs(u - n1 * n2 / 2), abs(uu - n1 * n2 / 2)
        if d > d0:
            piores += 1
        elif abs(d - d0) < 1e-9:
            iguais += 1
    return u, (piores + iguais) / total


def main():
    prov = json.loads(_raiz('proveniencia_das_operacoes.json').read_text())['proveniencia']
    val = json.loads(_raiz('o_que_cada_fonte_valida.json').read_text())['por_fonte']
    inv = json.loads(_raiz('quantas_invertem_ALEM_DO_ACASO.json').read_text())['por_operacao']

    linhas, sem_leitura = [], []
    for op, v in inv.items():
        fontes = prov.get(op)
        fontes = [fontes] if isinstance(fontes, str) else (fontes or [])
        tipos = {val[f]['tipo'] for f in fontes if f in val}
        if not tipos:
            sem_leitura.append(op)
            continue
        # ⚠️ uma operacao com mais de uma fonte so entra se as fontes concordarem no tipo
        if len(tipos) > 1:
            sem_leitura.append(op)
            continue
        linhas.append({'operacao': op, 'fontes': fontes, 'evidencia': tipos.pop(),
                       'tipos_abaixo': len(v['tipos_abaixo_de_50']),
                       'pior': v['menor_acuracia']})

    propriedade = [l['tipos_abaixo'] for l in linhas if l['evidencia'] == VALIDA_A_PROPRIEDADE]
    resumo = [l['tipos_abaixo'] for l in linhas if l['evidencia'] != VALIDA_A_PROPRIEDADE]
    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_desenho': 'observacional, n pequeno; descricao com teste declarado',
        'n_operacoes_classificadas': len(linhas),
        'nao_classificadas': sem_leitura,
        'por_operacao': sorted(linhas, key=lambda x: (x['evidencia'], x['tipos_abaixo'])),
        'grupos': {
            'valida_a_propriedade': {'n': len(propriedade), 'tipos_abaixo': sorted(propriedade),
                                     'mediana': sorted(propriedade)[len(propriedade) // 2] if propriedade else None},
            'nao_valida_a_propriedade': {'n': len(resumo), 'tipos_abaixo': sorted(resumo),
                                         'mediana': sorted(resumo)[len(resumo) // 2] if resumo else None},
        },
    }
    if len(propriedade) >= 3 and len(resumo) >= 3:
        u, p = mannwhitney_exato(propriedade, resumo)
        res['mannwhitney'] = {'U': u, 'p_exato_bilateral': round(p, 4), 'separa_a_005': p < .05}
        res['previsoes'] = {
            '1_n_suficiente': 'CONFIRMADA',
            '2_a_propriedade_inverte_menos':
                'CONFIRMADA' if p < .05 and (sorted(propriedade)[len(propriedade) // 2]
                                             < sorted(resumo)[len(resumo) // 2]) else '⛔ NAO SEPARA',
        }
    else:
        res['mannwhitney'] = None
        res['previsoes'] = {'1_n_suficiente': '⛔ FALHOU: %d contra %d'
                            % (len(propriedade), len(resumo)),
                            '2_a_propriedade_inverte_menos': 'NAO TESTAVEL'}
    res['⛔_NAO_ENTRA_NO_ARTIGO'] = (
        'o teste NAO separa (p %.4f) e o desenho tem 5 contra 7 operacoes: isto e um nulo '
        'SEM PODER, e reportar «nao ha diferenca» seria a troca de ausencia de evidencia por '
        'evidencia de ausencia que o proprio artigo evita em outros lugares. Fica arquivado: '
        'serve para impedir que alguem AFIRME a associacao sem medir, nao para negar ela.'
        % (res['mannwhitney']['p_exato_bilateral'] if res['mannwhitney'] else float('nan')))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print('  valida a propriedade:', sorted(propriedade), '| so o resumo:', sorted(resumo))
    if res['mannwhitney']:
        print('  Mann-Whitney U %.1f, p exato %.4f' % (res['mannwhitney']['U'],
                                                       res['mannwhitney']['p_exato_bilateral']))
    if sem_leitura:
        print('  fora da conta (sem leitura ou fontes discordantes):', sem_leitura)


if __name__ == '__main__':
    main()
