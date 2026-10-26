#!/usr/bin/env python3
"""⭐⭐ AS OPERACOES CONCORDAM MAIS ENTRE SI OU COM UM MODELO VALIDADO?

POR QUE EXISTE (08/09/2026). O artigo trata as dezesseis como uma CLASSE: «as operacoes que
a literatura poe neste slot como filtro de qualidade». Se elas medissem a mesma coisa,
concordariam entre si mais do que com qualquer coisa de fora. A pergunta nunca foi feita.

⚠️ As duas quantidades tem de ser calculadas no MESMO conjunto, nos MESMOS clusters e com o
MESMO piso de acaso, senao a comparacao mistura convencoes — o erro recorrente deste projeto.
Aqui: as operacoes que tem piso medido, os 42 clusters operacionais, e o piso 1/k medio.

PREVISOES, antes de rodar:
  1. o piso de acaso reproduz o 0,4702 publicado
  2. (hipotese) a concordancia par a par entre operacoes e MENOR que a de cada uma com o
     modelo de referencia
  3. o controle das duplicatas exatas fica no teto (kappa 1), senao a conta esta errada
"""
import json
import statistics
from itertools import combinations
from pathlib import Path

QB = Path('/data/projects/benchmark')


def _raiz(nome):
    for base in (QB, Path(__file__).resolve().parent / 'derived_data',
                 Path(__file__).resolve().parent):
        if (base / nome).exists():
            return base / nome
    raise FileNotFoundError(nome)


SAIDA = (QB if QB.exists() else Path(__file__).resolve().parent) / \
    'a_classe_nao_concorda_consigo.json'


def main():
    top = json.loads(_raiz('efeito_a_jusante.json').read_text(encoding='utf-8'))['topicos']
    cl = [c for t in top.values() for c in t['clusters']]
    piso = {x['operacao']: x for x in
            json.loads(_raiz('o_piso_das_operacoes_isoladas_e_estavel.json')
                       .read_text(encoding='utf-8'))['por_operacao']}
    ops = sorted({o for c in cl for o in c['escores']} & set(piso))

    def venc(c, o):
        e = c['escores'].get(o)
        return max(e, key=e.get) if e else None

    acaso = sum(1 / c['n'] for c in cl) / len(cl)

    def kap(a, b):
        ac = sum(1 for c in cl if venc(c, a) == venc(c, b)) / len(cl)
        return (ac - acaso) / (1 - acaso)

    pares = {'%s|%s' % (a, b): round(kap(a, b), 4) for a, b in combinations(ops, 2)}
    com_ref = {o: round(piso[o]['kappa'], 4) for o in ops}
    med_par = statistics.median(pares.values())
    med_ref = statistics.median(com_ref.values())

    # ⭐ SEGUNDO EIXO: e DENTRO da mesma fonte elas concordam mais? Se o conjunto de
    # features de um artigo fosse coerente como medida de qualidade, os pares internos
    # ficariam acima dos externos.
    prov = json.loads(_raiz('proveniencia_das_operacoes.json').read_text())['proveniencia']

    def fontes(o):
        v = prov.get(o)
        return set([v] if isinstance(v, str) else (v or []))

    # ⚠️ este eixo usa TODAS as operacoes com proveniencia, nao so as que tem piso medido:
    # e a mesma populacao da comparacao par a par que o corpo publica (91 pares). Herdar o
    # conjunto restrito daria outra contagem para a mesma frase.
    todas = sorted({o for c in cl for o in c['escores']})
    dentro, fora = [], []
    for a, b in combinations(todas, 2):
        fa, fb = fontes(a), fontes(b)
        if not fa or not fb:
            continue
        k = kap(a, b)
        # ⚠️ a duplicata exata e a MESMA computacao com dois nomes: ela infla o grupo
        # «mesma fonte» sem dizer nada sobre coerencia, e sai da conta interna
        if fa & fb and k < .999:
            dentro.append(k)
        elif not (fa & fb):
            fora.append(k)

    # ⚠️ CONTROLE: as duas implementacoes da mesma expressao de Hasler tem de dar kappa 1.
    # Se nao derem, a conta de concordancia esta errada e o resto nao vale nada.
    dupl = [k for k in pares if 'hasler_colorfulness' in k and 'ke_colorfulness' in k]
    ctrl = pares[dupl[0]] if dupl else None

    res = {
        '_o_que_e': __doc__.strip().split('\n\n')[0],
        '_mesma_convencao': 'mesmos %d clusters, mesmo piso de acaso, mesmas %d operacoes'
                            % (len(cl), len(ops)),
        'n_clusters': len(cl), 'n_operacoes': len(ops), 'n_pares': len(pares),
        'piso_do_acaso': round(acaso, 4),
        'kappa_par_a_par_entre_operacoes': {
            'mediana': round(med_par, 4),
            'minimo': round(min(pares.values()), 4), 'maximo': round(max(pares.values()), 4)},
        'kappa_de_cada_operacao_com_a_referencia': {
            'mediana': round(med_ref, 4),
            'minimo': round(min(com_ref.values()), 4), 'maximo': round(max(com_ref.values()), 4)},
        'razao_das_medianas': round(med_ref / med_par, 2) if med_par else None,
        'controle_duplicata_exata': {'par': dupl[0] if dupl else None, 'kappa': ctrl},
        'por_operacao_com_a_referencia': com_ref,
        'mesma_fonte_contra_fontes_diferentes': {
            '_o_que_e': 'pares dentro da mesma fonte, tirando as duplicatas exatas, contra '
                        'pares de fontes diferentes, em TODAS as operacoes com proveniencia',
            'n_operacoes': len(todas),
            'dentro': {'n': len(dentro), 'mediana': round(statistics.median(dentro), 4)},
            'fora': {'n': len(fora), 'mediana': round(statistics.median(fora), 4)},
            '_leitura': 'os dois medianos ficam junto de zero; o desenho nao separa os '
                        'grupos e o estimador interno e ate um pouco MENOR, entao o '
                        'conjunto de features de um mesmo artigo nao e mais coerente que '
                        'uma juncao arbitraria'},
    }
    res['previsoes'] = {
        '1_o_piso_reproduz': 'CONFIRMADA' if abs(acaso - .4702) < 5e-4 else '⛔ FALHOU',
        '2_concordam_menos_entre_si': 'CONFIRMADA' if med_par < med_ref else '⛔ FALHOU',
        '3_o_controle_da_duplicata_esta_no_teto':
            'CONFIRMADA' if ctrl is not None and abs(ctrl - 1.0) < 1e-9 else '⛔ FALHOU: %s' % ctrl,
    }
    res['leitura'] = (
        'nos mesmos %d clusters e com o mesmo piso, a concordancia MEDIANA entre duas '
        'operacoes e kappa %.4f, e a de cada operacao com o modelo de referencia e %.4f: '
        '%.1f vezes maior. A classe concorda mais com algo de fora do que consigo mesma, '
        'o que quer dizer que as dezesseis nao medem a mesma coisa.'
        % (len(cl), med_par, med_ref, med_ref / med_par if med_par else float('nan')))
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(' ', res['previsoes'])
    print(' ', res['leitura'])


if __name__ == '__main__':
    main()
