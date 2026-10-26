#!/usr/bin/env python3
"""AS MELHORES OPERACOES DA LITERATURA, ao lado do SIFT+BoVW na Tabela 4.

POR QUE EXISTE (25/09/2026, item 2). A Tabela 4 punha o SIFT+BoVW sozinho numa faixa e os
modelos NR-IQA noutra. Assim o leitor so compara a operacao da bancada com os modelos
dedicados, e nao com as outras operacoes da LITERATURA — que e a comparacao que o artigo
existe para fazer.

⭐ Entram as tres melhores da literatura pela media das oito, na mesma regua estrita da
Tabela 6. ⚠️ `hasler_colorfulness` e `ke_colorfulness` sao a MESMA funcao sob dois nomes
(a nota ‡ da Tabela 6), entao entra uma so.
"""
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'tab_construida_lit.tex'
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']
QUANTAS = 3
# ⛔ as duas colourfulness sao a mesma funcao: manter as duas fingiria duas evidencias
DUPLICATA = {'ke_colorfulness'}
NOME = {'srinivas_quality': r'Mean rule~\citep{srinivas2016rank}',
        'hasler_colorfulness': r'Colourfulness~\citep{hasler2003colorfulness}',
        'gygli_media_crua': r'Averaged aesthetics~\citep{gygli2014summe}',
        'glcm_contraste': 'GLCM contrast',
        'contraste_variancia': 'Grey-level dispersion'}


def main():
    d = json.loads((QB / 'ops_da_literatura_designA.json').read_text(encoding='utf-8'))['resumo_designA']
    cand = []
    for k, v in d.items():
        if k in DUPLICATA:
            continue
        m = dict(zip(v['ordem'], v['acuracia_por_tipo']))
        vals = [m.get(t) for t in TIPOS]
        if any(x is None for x in vals):
            continue
        cand.append((sum(vals) / 8, k, vals))
    cand.sort(reverse=True)
    top = cand[:QUANTAS]
    assert all(k in NOME for _, k, _ in top), [k for _, k, _ in top]

    L = []
    for media, k, vals in top:
        cels = []
        for x in vals:
            # a mesma marca da tabela: inversao descritiva em vermelho e negrito
            cels.append(r'\textcolor{accentred}{\textbf{%d}}' % round(x) if x < 50
                        else '%d' % round(x))
        L.append(r'%s & %s & \textbf{%.1f} \\' % (NOME[k], ' & '.join(cels), media))
    SAIDA.write_text('\n'.join(L)
                     + '\n%% GERADO por %s -- nao editar a mao\n' % Path(__file__).name)
    print('  %d operacoes da literatura -> %s (%s)'
          % (len(top), SAIDA.name, ', '.join('%s %.1f' % (k, m) for m, k, _ in top)))


if __name__ == '__main__':
    main()
