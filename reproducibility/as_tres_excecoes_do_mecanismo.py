#!/usr/bin/env python3
"""⭐ AS TRES EXCECOES DO MECANISMO SAO INVERSAO OU SAO EMPATE?

POR QUE EXISTE (08/09/2026). O corpo diz que o sinal da diferenca de escore segue o sinal da
diferenca de CONTAGEM em «797 dos 800 pares». Um revisor pergunta em seguida o que sao os
tres — e a resposta muda o estatuto da afirmacao: tres inversoes genuinas enfraquecem a
fatoracao, tres empates de margem nao.

Medido: as tres diferem por 4, 1 e 2 descritores, contra uma contagem MEDIANA de 1092 por
frame. Sao empates na pratica, nao contra-exemplos.

PREVISOES:
  1. as tres discordancias tem |delta_conta| pequeno em relacao a mediana
  2. nenhuma delas tem |delta_conta| acima de 1 % da mediana
"""
import json
import statistics
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
PAR = QB / 'a_contagem_reproduz_a_escolha_par_a_par.json'
SIFT = Path('/dados/Projetos/evaluality-mtap-submission/reproducibility/derived_data/synth_sift.json')
SAIDA = QB / 'as_tres_excecoes_do_mecanismo.json'


def contagens(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'n_desc' and isinstance(v, (int, float)):
                acc.append(v)
            else:
                contagens(v, acc)
    elif isinstance(o, list):
        for v in o:
            contagens(v, acc)


def main():
    d = json.loads(PAR.read_text(encoding='utf-8'))
    acc = []
    contagens(json.loads(SIFT.read_text(encoding='utf-8')), acc)
    mediana = statistics.median(acc)
    disc = d['onde_discordam']
    maior = max(abs(x['delta_conta']) for x in disc)
    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_fontes': [PAR.name, str(SIFT)],
        'pares': d['pares'], 'concordam': d['pares_em_que_score_e_contagem_concordam'],
        'discordam': len(disc),
        'n_desc_medida': {'n': len(acc), 'mediana': mediana, 'minimo': min(acc)},
        'maior_delta_de_contagem_entre_as_discordancias': maior,
        'como_fracao_da_mediana': round(maior / mediana, 6),
        'as_tres': [{'celula': x['celula'], 'delta_conta': x['delta_conta'],
                     'delta_score': x['delta_score']} for x in disc],
        'previsoes': {
            '1_sao_de_margem': 'CONFIRMADA' if maior <= 5 else '⛔ FALHOU',
            '2_abaixo_de_1_por_cento_da_mediana':
                'CONFIRMADA' if maior / mediana < .01 else '⛔ FALHOU'},
    }
    res['leitura'] = (
        'as %d discordancias diferem por no maximo %d descritores, contra uma contagem '
        'mediana de %d por frame (%.3f %% dela): sao empates de margem, nao inversoes.'
        % (len(disc), maior, mediana, 100 * maior / mediana))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
