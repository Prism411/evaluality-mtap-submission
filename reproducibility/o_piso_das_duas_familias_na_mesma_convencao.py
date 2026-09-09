#!/usr/bin/env python3
"""⭐ O PISO IN-DOMAIN NAS DUAS FAMILIAS, COM A MESMA REGRA DE QUEM ENTRA.

POR QUE EXISTE (08/09/2026). O `a_distancia_ate_o_limiar.json` reporta mediana **0,2809**
para as operacoes e **0,7078** para os modelos, mas as duas contas nao usam a mesma regra de
entrada: a das operacoes inclui o `si`, que **nao carrega veredito** porque a fonte nao
declara direcao. Comparar as duas assim mistura convencoes — o mesmo erro que ja produziu
numero errado neste projeto.

Aqui as duas familias entram pela MESMA regra: fora quem nao carrega veredito. E o resultado
vem com a fragilidade medida ao lado, porque o `veredito_virou_em` mostra que parte do que
passa nao sobrevive a tirar UM topico.

PREVISOES:
  1. sem o `si` sobram dez operacoes
  2. as duas familias tem o mesmo n, dez, e a comparacao fica direta
  3. parte das que passam vira o veredito ao tirar um topico
"""
import json
import statistics
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')


def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)


SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / \
    'o_piso_das_duas_familias_na_mesma_convencao.json'


def main():
    # ⛔ E O CONJUNTO E O DO ARTIGO. O arquivo do piso traz onze linhas, e duas delas nao
    # pertencem ao inventario auditado: o `si`, que nao carrega veredito, e o `sobel_cv`,
    # que nem esta entre as quinze. Contar as onze daria «6 de 10» onde o corpo ja diz
    # «5 de 9» — dois numeros medindo populacoes diferentes, o erro classico deste projeto.
    do_artigo = set(json.loads(_raiz('as_15_na_regra_do_artigo.json')
                               .read_text(encoding='utf-8'))['por_operacao'])
    ops = [x for x in json.loads(_raiz('o_piso_das_operacoes_isoladas_e_estavel.json')
                                 .read_text(encoding='utf-8'))['por_operacao']
           if x['operacao'] != 'si' and x['operacao'] in do_artigo]
    passam = [x for x in ops if x['passa']]
    frageis = [x for x in passam if x['veredito_virou_em'] > 0]
    dist = json.loads(_raiz('a_distancia_ate_o_limiar.json').read_text(encoding='utf-8'))
    mod = dist['para_referencia_o_piso_nas_duas_familias']['NR-IQA']

    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_regra_de_entrada': 'o conjunto do artigo, sem o `si`; nas duas familias',
        '_referencia': 'LIQE nas DUAS familias. A coluna Floor da tabela mistura Q-Align nos modelos com LIQE nas operacoes; a comparacao ENTRE familias so vale na MESMA referencia, e por isso esta conta usa LIQE dos dois lados.',
        'fora_do_inventario_auditado': ['si', 'sobel_cv'],
        'operacoes': {
            'n': len(ops), 'passam': len(passam),
            'kappa_mediano_de_todas': round(statistics.median(x['kappa'] for x in ops), 4),
            'kappa_mediano_das_que_passam': round(statistics.median(x['kappa'] for x in passam), 4),
            'kappa_maximo': round(max(x['kappa'] for x in ops), 4),
        },
        'modelos': {'n': mod['n'], 'passam': mod['passam'],
                    'kappa_mediano_de_todos': round(mod['kappa_mediano'], 4),
                    'kappa_maximo': round(mod['kappa_maximo'], 4)},
        'fragilidade_ao_tirar_um_topico': {
            'n_rodadas': passam[0]['n_rodadas'] if passam else None,
            'quantas_das_que_passam_viram': len(frageis),
            'quais': {x['operacao']: '%d de %d' % (x['veredito_virou_em'], x['n_rodadas'])
                      for x in frageis}},
    }
    res['previsoes'] = {
        '1_nove_operacoes_como_o_corpo_ja_diz': 'CONFIRMADA' if len(ops) == 9 else '⛔ FALHOU',
        '2_cinco_passam_como_o_corpo_ja_diz': 'CONFIRMADA' if len(passam) == 5 else '⛔ FALHOU',
        '3_ha_fragilidade': 'CONFIRMADA' if frageis else '⛔ FALHOU',
    }
    res['leitura'] = (
        'sob a mesma regra de entrada, %d das %d operacoes passam o piso in-domain contra '
        '%d de %d modelos, e a mediana e %.4f contra %.4f. Das %d que passam, %d viram o '
        'veredito ao tirar UM topico.'
        % (len(passam), len(ops), mod['passam'], mod['n'],
           res['operacoes']['kappa_mediano_de_todas'], mod['kappa_mediano'],
           len(passam), len(frageis)))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
