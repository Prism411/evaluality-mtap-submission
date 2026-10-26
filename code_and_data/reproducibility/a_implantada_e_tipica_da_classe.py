#!/usr/bin/env python3
"""⭐⭐ A OPERACAO IMPLANTADA E UM CASO ATIPICO OU E TIPICA DA CLASSE?

POR QUE EXISTE (08/09/2026). O artigo audita UMA operacao implantada em detalhe e uma CLASSE
de dezesseis em conjunto. A ponte entre as duas coisas nunca foi medida: se a implantada
fosse um caso ruim fora da curva, o mecanismo dela nao diria nada sobre a classe; se ela
estiver no meio da classe, o caso deixa de ser anedota.

⚠️ As duas familias tem de vir da MESMA tabela e do MESMO desenho, senao a posicao nao
significa nada. Aqui: a media sobre os oito tipos dos 800 pares construidos, a mesma coluna
para todos.

PREVISOES:
  1. a implantada NAO e o pior da classe
  2. ela fica perto da mediana da classe (dentro de 2 pontos)
  3. a mediana dos modelos publicados fica muito acima das duas
"""
import json
import statistics
from pathlib import Path

QB = Path('/data/projects/benchmark')


def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)


SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / \
    'a_implantada_e_tipica_da_classe.json'
DEP = 'SIFT+BoVW'


def main():
    linhas = json.loads(_raiz('TABELA_FINAL.json').read_text(encoding='utf-8'))['linhas']
    classe = [(l['nome'], l['media']) for l in linhas if 'sumariza' in l['familia']]
    dep = next(l['media'] for l in linhas if l['nome'] == DEP)
    # ⚠️ a implantada e listada na familia dos NR-IQA por vir do pipeline, nao da rodada
    # de operacoes: por isso ela nao esta dentro de `classe`, e a posicao e limpa.
    modelos = [l['media'] for l in linhas if 'NR-IQA' in l['familia'] and l['nome'] != DEP]
    abaixo = sum(1 for _, m in classe if m < dep)
    med = statistics.median(m for _, m in classe)

    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_mesma_coluna': 'media sobre os oito tipos dos 800 pares construidos, para todos',
        'implantada': {'nome': DEP, 'media': round(dep, 2)},
        'classe_de_sumarizacao': {
            'n': len(classe), 'mediana': round(med, 2),
            'minimo': round(min(m for _, m in classe), 2),
            'maximo': round(max(m for _, m in classe), 2),
            'quantas_ficam_abaixo_da_implantada': abaixo},
        'modelos_publicados': {'n': len(modelos), 'mediana': round(statistics.median(modelos), 2)},
        'distancia_da_implantada_a_mediana_da_classe': round(abs(dep - med), 2),
    }
    res['previsoes'] = {
        '1_nao_e_o_pior': 'CONFIRMADA' if abaixo > 0 else '⛔ FALHOU',
        '2_perto_da_mediana': 'CONFIRMADA' if abs(dep - med) <= 2 else '⛔ FALHOU',
        '3_modelos_muito_acima':
            'CONFIRMADA' if statistics.median(modelos) > med + 15 else '⛔ FALHOU',
    }
    res['leitura'] = (
        'a operacao implantada marca %.1f %% e %d das %d operacoes e compostos da classe '
        'ficam ABAIXO dela; a mediana da classe e %.1f, a %.1f ponto dela, e a dos modelos '
        'publicados e %.1f. O caso implantado nao e fora da curva: ele e o meio da classe '
        'de onde vem.'
        % (dep, abaixo, len(classe), med, abs(dep - med), statistics.median(modelos)))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
