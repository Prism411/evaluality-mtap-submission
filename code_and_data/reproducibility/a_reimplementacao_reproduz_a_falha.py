#!/usr/bin/env python3
"""⭐⭐ UMA REIMPLEMENTACAO INDEPENDENTE DA OPERACAO IMPLANTADA REPRODUZ A FALHA?

POR QUE EXISTE (08/09/2026). A objecao mais forte contra auditar o sistema de outra pessoa e
«voces implementaram errado». O artigo mede a operacao implantada pela rodada REPORTADA
(65,1 %); existe uma segunda rodada, uma reimplementacao independente do SIFT+BoVW no mesmo
desenho, e comparar as duas responde a objecao com numero.

⚠️ E a resposta nao e «igual»: as duas concordam em dois dos tres tipos que colapsam e
DIVERGEM no terceiro. Reportar «reproduz» sem dizer onde diverge seria esconder o unico
lugar em que a implementacao importa.

PREVISOES, antes de rodar:
  1. as duas rodadas tem os mesmos 800 pares
  2. as duas colapsam em ruido e JPEG
  3. a media da reimplementacao fica MUITO abaixo do pior modelo publicado (80,8)
"""
import json
from pathlib import Path

QB = Path('/data/projects/benchmark')


def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)


SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / \
    'a_reimplementacao_reproduz_a_falha.json'
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']


def main():
    s = json.loads(_raiz('sift_designA.json').read_text(encoding='utf-8'))['por_segmento']
    linhas = {l['nome']: l for l in json.loads(_raiz('TABELA_FINAL.json').read_text())['linhas']}
    rep = linhas['SIFT+BoVW']['acc']
    pior_modelo = min(l['media'] for n, l in linhas.items()
                      if 'NR-IQA' in l['familia'] and n != 'SIFT+BoVW')

    reimp, cert, tot = {}, 0, 0
    for t in TIPOS:
        c = n = 0
        for v in s.values():
            for lv in range(1, 6):
                cel = v.get('%s_%d' % (t, lv))
                if not cel or cel['orig'] == cel['deg']:
                    continue
                n += 1
                c += int(cel['orig'] > cel['deg'])
        reimp[t] = round(100 * c / n, 1) if n else None
        cert += c
        tot += n
    media = 100 * cert / tot

    colapsam_rep = [t for t in TIPOS if rep[t] < 50]
    colapsam_re = [t for t in TIPOS if reimp[t] is not None and reimp[t] < 50]
    comuns = [t for t in colapsam_rep if t in colapsam_re]
    so_rep = [t for t in colapsam_rep if t not in colapsam_re]

    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        'n_pares': tot,
        'reportada': {'por_tipo': rep, 'media': round(linhas['SIFT+BoVW']['media'], 2)},
        'reimplementacao': {'por_tipo': reimp, 'media': round(media, 2)},
        'colapsam_nas_duas': comuns,
        '⚠️_colapsam_so_na_reportada': so_rep,
        'pior_modelo_publicado': round(pior_modelo, 1),
        'previsoes': {
            '1_mesmos_800_pares': 'CONFIRMADA' if tot == 800 else '⛔ FALHOU: %d' % tot,
            '2_colapsam_em_ruido_e_jpeg':
                'CONFIRMADA' if {'noise', 'jpeg'} <= set(comuns) else '⛔ FALHOU',
            '3_abaixo_do_pior_modelo':
                'CONFIRMADA' if media < pior_modelo else '⛔ FALHOU'},
    }
    res['leitura'] = (
        'a reimplementacao independente marca %.1f %% contra %.1f %% da rodada reportada, '
        'e colapsa nos mesmos %s. ⚠️ Diverge em %s, onde a reportada inverte (%s %%) e a '
        'reimplementacao fica em %s %%. As duas ficam abaixo do pior modelo publicado, %.1f.'
        % (media, linhas['SIFT+BoVW']['media'], ' e '.join(comuns),
           ' e '.join(so_rep) or 'nenhum tipo',
           ', '.join(str(rep[t]) for t in so_rep) or '-',
           ', '.join(str(reimp[t]) for t in so_rep) or '-', pior_modelo))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
