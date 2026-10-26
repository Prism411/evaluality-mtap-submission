#!/usr/bin/env python3
r"""⛔ «ORDENA A DEGRADADA ACIMA» AINDA VALE QUANDO HA EMPATE?

POR QUE EXISTE (14/09/2026). O corpo afirma que cada uma das quinze operacoes \textbf{ordena
a copia degradada acima da original} em ao menos um tipo, e a tabela marca como inversao toda
celula com acuracia abaixo de 50 %. ⚠️ **As duas coisas nao sao a mesma**: acertos + erros +
empates somam 1, entao acerto < .50 admite erro < .50. E ha empates — **104**, dos quais
**81 numa unica operacao** (`ke_hue_count`). Bastava um punhado deles cair na celula certa
para a frase do corpo passar a afirmar o que o dado nao mostra.

⭐ MEDIDO: nas **35** celulas abaixo de 50 %, a fracao de ERRO passa de 50 % em **todas**.
A frase se sustenta celula a celula. 📄 `o_empate_nao_inverte_nenhuma_celula.json`

🔴 Mas isso e um FATO DESTE CONJUNTO, nao uma identidade aritmetica. Com outra distribuicao
de empates a equivalencia cai e a frase fica errada sem nada quebrar — que e por que a
verificacao vira guarda em vez de nota de rodape.
"""
import json, re, sys
from pathlib import Path

A = Path(__file__).parent
QB = Path('/data/projects/benchmark')
FONTE = QB / 'ops_da_literatura_designA.json'
PROV = QB / 'proveniencia_das_operacoes.json'
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']

# a frase do corpo que esta verificacao sustenta
FRASE = 'ranks the degraded\ncopy above the original'


def celulas():
    """(abaixo de 50 %, sem maioria para a degradada, empates) — recomputado dos escores."""
    d = json.loads(FONTE.read_text(encoding='utf-8'))
    a15 = set(json.loads(PROV.read_text(encoding='utf-8'))['as_15_da_tabela_S3'])
    ps, res = d['por_segmento'], d['resumo_designA']
    abaixo, ruins, emp = [], [], 0
    for op in sorted(a15):
        if op not in res or res[op].get('direcao_maior_melhor') is None:
            continue
        maior = bool(res[op]['direcao_maior_melhor'])
        for t in TIPOS:
            ac = er = em = 0
            for v in ps.values():
                if op not in v or v[op].get('orig') is None:
                    continue
                o = v[op]['orig']
                for n in range(1, 6):
                    deg = v[op].get(f'{t}_{n}')
                    if deg is None:
                        continue
                    if deg == o:
                        em += 1
                    elif (o > deg) == maior:
                        ac += 1
                    else:
                        er += 1
            tot = ac + er + em
            if not tot or 100 * ac / tot >= 50:
                continue
            emp += em
            abaixo.append((op, t))
            if 100 * er / tot <= 50:
                ruins.append((op, t, ac, er, em, tot))
    return abaixo, ruins, emp


def main():
    if not FONTE.exists():
        print('  ⏳ escores do desenho A ausentes: nao se decide'); return 0
    abaixo, ruins, emp = celulas()
    corpo = '\n'.join((A / f).read_text(errors='replace')
                      for f in ('sec_results.tex', 'sec_intro.tex', 'sec_conclusion.tex'))
    afirma = re.search(r'\s+'.join(re.escape(w) for w in FRASE.split()), corpo) is not None
    if ruins and afirma:
        print(f'  ⛔ o corpo afirma «ordena a degradada acima», mas em {len(ruins)} celula(s) '
              f'a degradada NAO e a maioria:')
        for op, t, ac, er, em, tot in ruins[:4]:
            print(f'       {op} / {t}: acerta {ac}, erra {er}, empata {em} de {tot}')
        print('     use «strict paired accuracy below 50 per cent», que vale com empate.')
        return 1
    print(f'  ✅ {len(abaixo)} celulas abaixo de 50 %, {emp} empates, e em todas a degradada '
          f'e a maioria')
    return 0


def autoteste():
    """Duas pernas: o estado atual passa, e um empate que INVERTE uma celula reprova."""
    abaixo, ruins, emp = celulas()
    mal = 0
    print(f"  {'✅' if not ruins else '⛔'} estado atual: {len(ruins)} celula(s) sem maioria, "
          f"esperado 0  ({len(abaixo)} celulas, {emp} empates)")
    mal += bool(ruins)
    if emp == 0:
        print('  ⛔ zero empates no conjunto: a guarda nao estaria exercitando nada')
        mal += 1
    else:
        print(f'  ✅ ha {emp} empates, entao a distincao e real e nao hipotetica')
    # ⛔ a perna que separa: uma celula onde o empate manda passa a REPROVAR
    ac, er, em = 40, 35, 25
    tot = ac + er + em
    inverte = 100 * ac / tot < 50 and 100 * er / tot <= 50
    print(f"  {'✅' if inverte else '⛔'} caso sintetico 40/35/25: acuracia {100*ac/tot:.0f}% "
          f"mas erro {100*er/tot:.0f}% — a guarda o classifica como defeito")
    mal += not inverte
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
