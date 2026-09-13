"""⛔ TROCAR DESVIO-PADRAO POR VARIANCIA NO `contraste_variancia` MUDA A TABELA?

POR QUE EXISTE (13/09/2026, segundo parecer do MTAP). A Tabela S23 dizia «pixel variance» e
o codigo computa `gray.std()`. ⭐ O revisor apontou o que importa, e o argumento dele e
correto: DENTRO de um frame as duas ordenam identicamente, mas a operacao agrega a MEDIA
SOBRE FRAMES, e ai a equivalencia cai. O contraexemplo dele:

    segmento A, desvios 0 e 10  ->  media dos desvios 5,  media das variancias 50
    segmento B, desvios 6 e 6   ->  media dos desvios 6,  media das variancias 36

A ordem entre A e B inverte conforme o que se agrega.

📌 ISTO NAO E UM EXPERIMENTO NOVO: e a mesma tabela dos 800 pares, com a operacao trocada
pela que a S23 anunciava. Os frames sao reconstruidos EM MEMORIA pelo `synth_rebuild.py`,
que existe para isso; nada e re-extraido para disco.

⚠️ PRE-CONDICAO: reproduzir a acuracia publicada do `contraste_variancia` com o desvio
antes de comparar. Sem isso eu nao sei se estou na mesma tabela.

⭐ PREVISOES DECLARADAS ANTES DE RODAR:
 1. A acuracia MUDA, porque a agregacao nao e invariante.
 2. Muda POUCO, porque a media sobre frames de um mesmo segmento tem dispersao baixa.
 3. O veredito da linha (reprovar as portas) NAO muda.
"""
import json
import sys
from pathlib import Path

import numpy as np

H = Path('/dados/Projetos/quality-benchmark')
sys.path.insert(0, str(H))
import cv2  # noqa: E402
import synth_rebuild as RB  # noqa: E402

VAULT = Path('/home/jader/Desktop/estudos/osirihs/vault-5-sumarizador/iqa/medicoes/dados')


def std_do_frame(bgr):
    return float(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).std())


def main():
    pub = json.load(open(H / 'ops_da_literatura_designA.json'))['resumo_designA']
    assert 'contraste_variancia' in pub, '⛔ a operacao nao esta no resumo publicado'
    ref = pub['contraste_variancia']
    ORDEM = ref['ordem']
    acc_pub = ref['acuracia_por_tipo']

    std_, var_ = {}, {}
    n_seg = 0
    for s, p_, a, b in RB.segmentos_avaliados():
        c = RB.condicoes(p_, a, b)
        if not c:
            continue
        n_seg += 1
        for cond, frames in c.items():
            d = np.array([std_do_frame(f) for f in frames], float)
            std_['%s|%s' % (s, cond)] = float(d.mean())
            var_['%s|%s' % (s, cond)] = float((d ** 2).mean())
        print('   %s' % s, flush=True)
    print('  segmentos reconstruidos: %d' % n_seg)

    def por_tipo(esc):
        """Acuracia por tipo de degradacao: maior-melhor, o orig tem de vencer."""
        ac, muda = {}, 0
        for tipo in ORDEM:
            ok = tot = 0
            for k in esc:
                seg, cond = k.rsplit('|', 1)
                if not cond.startswith(tipo + '_'):
                    continue
                o = esc.get('%s|orig' % seg)
                if o is None:
                    continue
                tot += 1
                ok += int(o > esc[k])
            ac[tipo] = round(100.0 * ok / tot, 1) if tot else None
        return ac

    a_std, a_var = por_tipo(std_), por_tipo(var_)
    # quantos pares individuais trocam de lado
    muda = 0
    for k in std_:
        seg, cond = k.rsplit('|', 1)
        if cond == 'orig':
            continue
        if (std_['%s|orig' % seg] > std_[k]) != (var_['%s|orig' % seg] > var_[k]):
            muda += 1
    n_pares = sum(1 for k in std_ if not k.endswith('|orig'))

    rec = [a_std[t] for t in ORDEM]
    reproduz = all(abs(x - y) < 0.05 for x, y in zip(rec, acc_pub))
    m_std = round(sum(rec) / len(rec), 1)
    m_var = round(sum(a_var[t] for t in ORDEM) / len(ORDEM), 1)

    out = {
        '_o_que_e': '⛔ A operacao `contraste_variancia` sob as DUAS agregacoes: media dos '
                    'desvios (o que o codigo roda) e media das variancias (o que a Tabela '
                    'S23 anunciava). Mesma tabela de 800 pares, frames reconstruidos em '
                    'memoria pelo synth_rebuild; nada re-extraido para disco.',
        'unidade_de_reamostragem': 'par original-degradado',
        'n_segmentos': n_seg, 'n_pares': n_pares, 'ordem_dos_tipos': ORDEM,
        'PRE_CONDICAO': {
            'acuracia_publicada_por_tipo': acc_pub,
            'recomputada_com_desvio': rec,
            'reproduz': bool(reproduz),
        },
        'COM_A_MEDIA_DOS_DESVIOS': {'por_tipo': a_std, 'media': m_std},
        'COM_A_MEDIA_DAS_VARIANCIAS': {'por_tipo': a_var, 'media': m_var},
        'pares_que_mudam_de_lado': muda,
        'delta_na_media_em_pontos': round(m_var - m_std, 1),
    }
    out['PREVISOES'] = {
        '1_muda': muda > 0,
        '2_muda_pouco': abs(m_var - m_std) < 5.0,
        '3_veredito_por_tipo_nao_muda': all(
            (a_std[t] < 50) == (a_var[t] < 50) for t in ORDEM),
    }
    out['leitura'] = (
        'Trocar a media dos desvios pela media das variancias move %d dos %d pares de lado '
        'e a media por tipo em %+.1f ponto(s); o veredito por tipo (acima ou abaixo de 50) '
        '%s. ⛔ A equivalencia entre desvio e variancia so vale DENTRO de um frame: a '
        'operacao agrega sobre frames, e por isso o nome impresso tem de ser o da '
        'quantidade que de fato roda.'
        % (muda, n_pares, m_var - m_std,
           'NAO muda em nenhum tipo' if out['PREVISOES']['3_veredito_por_tipo_nao_muda']
           else 'MUDA em algum tipo'))
    json.dump(out, open(H / 'o_contraste_como_variancia_muda_a_tabela.json', 'w'),
              indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
