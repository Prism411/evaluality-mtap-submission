#!/usr/bin/env python3
"""OS DEZESSETE NA REGUA CANONICA — a mesma da Tabela 6 do corpo.

POR QUE EXISTE (25/09/2026, parecer v9, §1.1). O revisor achou a Tabela 6 e a S32
dando acuracias diferentes para as MESMAS operacoes sobre os MESMOS 800 pares, e
tratou como bloqueio de submissao. Estava certo em bloquear.

⭐ O QUE SE APUROU: nao ha duas rodadas. As acuracias POR TIPO sao identicas nos dois
arquivos. O que diverge sao DUAS escolhas de agregacao, independentes entre si:

  1. EMPATE. `ops_da_literatura_designA.json` conta empate como erro — acuracia
     ESTRITA, que e o que a legenda da Tabela 6 declara. O `TABELA_FINAL.json` tira
     empate do denominador (decisiva). So muda onde ha empate.
  2. ESCOPO DA MEDIA. O `TABELA_FINAL.media` exclui os tipos ALINHADOS POR CONSTRUCAO,
     que sao OUTROS em cada operacao. A Tabela 6 usa as oito em todas as linhas.

⛔ A S32 publicou as DUAS escolhas nao canonicas ao mesmo tempo, sob a legenda da
Tabela 6 — e com um IC que cerca a media COM exclusao, ao lado de uma acuracia sem
ela. As duas se movem em sentidos contrarios (empate sobe, exclusao desce), e e por
isso que a S32 saia ora acima ora ABAIXO da Tabela 6, como o revisor notou.

⭐ CANONICA = estrita, media sobre as OITO, de `ops_da_literatura_designA.json`. E a
que a legenda da Tabela 6 declara, e a decisao de 08/09 (`gera_tab_sintese.py`) fixa:
excluir tipos diferentes por linha faz as linhas deixarem de ser comparaveis entre si,
que e a unica coisa que uma coluna de media serve para fazer.

⚠️ `qaroush_movimento` nao esta no `resumo_designA` (e operacao de SEQUENCIA, fora do
inventario de quadro isolado), so nos escores crus. Recomputo aqui, e o CONTROLE e
reproduzir o `sobel_cv` publicado celula a celula antes de usar qualquer numero.
"""
import json
from pathlib import Path

QB = Path(__file__).parent
TIPOS = ['dark', 'motion', 'blur', 'h264', 'rescale', 'satur', 'noise', 'jpeg']
NIVEIS = 5


def acuracia_estrita(por_seg, op, maior_melhor):
    """Acuracia ESTRITA por tipo: empate conta como erro, como no designA."""
    out = {}
    for tp in TIPOS:
        acertos = total = 0
        for seg in por_seg.values():
            if op not in seg:
                continue
            e = seg[op]
            # ⚠️ duas formas no arquivo: umas operacoes tem UM `orig` por segmento, outras
            # um `orig_por_par` com o escore do original recomputado para cada par. Usar o
            # `orig` unico onde existe o `orig_por_par` erra a comparacao em silencio.
            por_par = e.get('orig_por_par')
            for lv in range(1, NIVEIS + 1):
                ch = '%s_%d' % (tp, lv)
                d = e.get(ch)
                if d is None:
                    continue
                o = por_par.get(ch) if isinstance(por_par, dict) else e.get('orig')
                if o is None:
                    continue
                total += 1
                acertos += int((o > d) if maior_melhor else (o < d))
        out[tp] = 100.0 * acertos / total if total else None
    return out


def main():
    d = json.loads((QB / 'ops_da_literatura_designA.json').read_text(encoding='utf-8'))
    por_seg, resumo = d['por_segmento'], d['resumo_designA']

    # ⛔ CONTROLE: o recomputo tem de reproduzir uma operacao PUBLICADA, celula a celula.
    ctrl = 'sobel_cv'
    esperado = dict(zip(resumo[ctrl]['ordem'], resumo[ctrl]['acuracia_por_tipo']))
    obtido = acuracia_estrita(por_seg, ctrl, resumo[ctrl]['direcao_maior_melhor'])
    assert all(abs(obtido[t] - esperado[t]) < 0.05 for t in TIPOS), \
        '⛔ o recomputo NAO reproduz o %s publicado: %s x %s' % (ctrl, obtido, esperado)

    # a direcao do movimento: a mesma que o TABELA_FINAL usou, conferida por reproducao
    # da acuracia DECISIVA dele nos tipos sem empate
    fin = {r['nome']: r for r in
           json.loads((QB / 'TABELA_FINAL.json').read_text(encoding='utf-8'))['linhas']}
    mov = 'qaroush_movimento'
    melhor = None
    for cand in (True, False):
        a = acuracia_estrita(por_seg, mov, cand)
        # estrita <= decisiva, e igual onde nao ha empate; a direcao certa e a que nao
        # ultrapassa a decisiva publicada em tipo nenhum
        if all(a[t] <= fin[mov]['acc'][t] + 0.05 for t in TIPOS):
            melhor = cand if melhor is None else '⛔ambigua'
    assert melhor in (True, False), \
        '⛔ nao consegui fixar a direcao de %s contra a decisiva publicada' % mov

    membros = {}
    q = json.loads((QB / 'quem_sao_os_dezessete.json').read_text(encoding='utf-8'))
    for m in q['membros']:
        n = m['nome']
        if n in resumo:
            pt = dict(zip(resumo[n]['ordem'], resumo[n]['acuracia_por_tipo']))
            origem = 'resumo_designA'
        else:
            pt = acuracia_estrita(por_seg, n, melhor)
            origem = 'recomputado dos escores crus, controle sobel_cv'
        vals = [x for x in pt.values() if x is not None]
        assert len(vals) == 8, (n, pt)
        # ⭐ a regua RIVAL do mesmo membro, para a tabela poder mostrar as duas e o
        #    leitor ver que a diferenca e de agregacao, nao de medicao
        r = fin.get(n)
        al = r.get('alinhados', []) if r else []
        rest = [tp for tp in r['acc'] if tp not in al] if r else []
        membros[n] = {'por_tipo': pt, 'media_estrita_oito': sum(vals) / 8,
                      'no_inventario_direcional': m['no_inventario_direcional'],
                      'origem': origem, 'n_comparacoes': 800,
                      'rival_decisiva_sem_alinhados': r['media'] if r else None,
                      'rival_tipos_excluidos': sorted(al),
                      'rival_n_comparacoes': 100 * len(rest) if r else None}

    imp = q['implantada_pct']
    def agrega(sel):
        v = sorted(membros[n]['media_estrita_oito'] for n in sel)
        return {'n': len(v), 'abaixo': sum(1 for x in v if x < imp),
                'mediana': v[len(v) // 2], 'minimo': v[0], 'maximo': v[-1]}

    dezessete = agrega(list(membros))
    quinze = agrega([n for n in membros if membros[n]['no_inventario_direcional']])

    # ⭐ CONTROLE DO REVISOR: refazendo a conta pelas medias da Tabela 6, ele obteve
    # mediana 74,8 nas quinze. A regua canonica TEM de reproduzir isso.
    assert abs(quinze['mediana'] - 74.75) < 0.06, \
        '⛔ as quinze nao dao a mediana 74,8 que a Tabela 6 impressa produz: %s' % quinze

    saida = {
        '_o_que_e': __doc__.strip(),
        '_regua': ('acuracia ESTRITA (empate conta como erro), media sobre as OITO '
                   'degradacoes — a mesma da Tabela 6 do corpo'),
        'implantada_pct': imp,
        'direcao_movimento_maior_melhor': melhor,
        'dezessete': dezessete,
        'quinze_do_inventario_direcional': quinze,
        'fora_do_inventario_direcional': q['fora_do_inventario_direcional'],
        'membros': membros,
        '_a_regua_rival': {
            '_o_que_e': ('a do TABELA_FINAL.media: decisiva E com os tipos alinhados por '
                         'construcao fora. Fica como SENSIBILIDADE, nunca como a coluna '
                         'principal: ela exclui celulas diferentes em cada linha.'),
            'dezessete': {'abaixo': q['abaixo_da_implantada'], 'mediana': q['mediana']},
            'quinze': {'abaixo': q['sem_os_extras']['abaixo'],
                       'mediana': q['sem_os_extras']['mediana']},
        },
    }
    (QB / 'os_dezessete_na_regua_da_tabela6.json').write_text(
        json.dumps(saida, ensure_ascii=False, indent=1), encoding='utf-8')
    print('controle sobel_cv ✅   direcao movimento maior_melhor=%s' % melhor)
    print('DEZESSETE  %s' % dezessete)
    print('QUINZE     %s' % quinze)
    print('rival (S32 atual)  dezessete: %d abaixo, mediana %.1f' %
          (q['abaixo_da_implantada'], q['mediana']))


if __name__ == '__main__':
    main()
