#!/usr/bin/env python3
r"""⛔ DOIS CONJUNTOS DO MESMO TAMANHO, CHAMADOS PELO MESMO NOME.

POR QUE EXISTE (15/09/2026). O corpo dizia «all ten models clear the floor», e a Secao 3.3
lista «ten NR-IQA candidates». **Sao conjuntos diferentes com o mesmo tamanho**: no piso o
LIQE sai, porque e a REFERENCIA daquela conta, e o **ARNIQA entra** — embora o artigo declare
que o ARNIQA e reportado so em eixos completos e nao participa da afirmacao complete-case.

🔴 Nada revelava isso. Os dois grupos tem dez membros, a mediana esta certa para o grupo que
o arquivo mede, e a frase compilava. Um leitor que voltasse a Secao 3.3 encontraria OUTROS
dez e nao teria como saber. ⚠️ Foi um parecer suspeitando de outra coisa (LIQE contra si
mesmo, que NAO acontece) que me fez abrir o arquivo.

⭐ A guarda: quando duas populacoes do artigo tem o mesmo tamanho, a diferenca entre elas
tem de estar ESCRITA. Aqui, que o grupo do piso troca LIQE por ARNIQA.
📄 `os_dez_do_piso_nao_sao_os_dez_candidatos.json`
"""
import json, re, sys
from pathlib import Path

A = Path(__file__).parent
QB = Path('/data/projects/benchmark')
PISO = QB / 'piso_as_duas_familias.json'

# a frase do corpo que tem de declarar a diferenca, e os termos que a tornam explicita
EXIGE = [r'ARNIQA',
         # ⚠️ 22/09 (parecer v2, V2-065): o paragrafo virou dois e a frase passou a dizer
         #    «LIQE is the designated reference for the literature-derived operations».
         #    O FATO exigido e o mesmo: que ali o LIQE e referencia, nao candidato.
         r'LIQE (?:is the (?:designated )?reference|as the reference)',
         r'nine other complete-case|not the complete-case\s*\n?candidate set']


def conjuntos():
    """(metodos do piso, candidatos da Secao 3.3), normalizados."""
    pm = json.loads(PISO.read_text(encoding='utf-8'))['por_metodo']
    piso = [k for k, v in pm.items() if v['familia'] == 'NR-IQA']
    t = (A / 'sec_method.tex').read_text(encoding='utf-8')
    # ⚠️ 21/09: o padrao exigia «ten NR-IQA candidates» coladas. Ao cumprir o criterio 27
    #    (sigla por extenso na primeira ocorrencia) a frase virou «ten no-reference image
    #    quality assessment (NR-IQA) candidates», e o leitor parou de achar a lista —
    #    reprovando por «bug do leitor» uma lista que estava escrita.
    # ⚠️ 22/09: o «ten» virou \invModelos{} na reescrita do parecer v3, pela regra de
    #    que todo numero entra por macro. A lista continua escrita logo depois.
    m = re.search(r'(?:ten|\\invModelos\{\})\s+(?:no-reference[^:]*?)?(?:\(NR-IQA\)\s+)?(?:candidates|models):\s*(.*?)\.',
                  re.sub(r'\s+', ' ', t), re.S)
    if not m:
        return piso, None
    cand = [x.strip() for x in re.sub(r'\s+', ' ', m.group(1)).replace(' and ', ', ').split(',')]
    norm = lambda s: (s.lower().replace('-', '').replace('$+$', '+')
                      .replace('_nr', '').replace(' ', ''))
    return {norm(x) for x in piso}, {norm(x) for x in cand if x}


def _texto():
    return '\n'.join((A / f).read_text(encoding='utf-8')
                     for f in ('sec_results.tex', 'supplementary.tex'))


def confere(corpo=None):
    piso, cand = conjuntos()
    if cand is None:
        return ['a lista de candidatos da Secao 3.3 nao foi encontrada: bug do leitor']
    if piso == cand:
        return []                       # nao ha ambiguidade a declarar
    if len(piso) != len(cand):
        return []                       # tamanhos diferentes: o leitor percebe sozinho
    # ⚠️ 28/09 (cli-3): a comparacao de referencia comum (o SEGUNDO grupo de dez) foi para o
    # suplementar com o benchmark de modelo; a declaracao tem de estar onde o grupo aparece.
    t = corpo if corpo is not None else _texto()
    faltam = [p for p in EXIGE if not re.search(p, t, re.I)]
    if faltam:
        return ['os dois grupos tem %d membros e diferem (%s x %s), mas o corpo nao declara '
                'a diferenca: falta %s' % (len(piso), sorted(piso - cand), sorted(cand - piso),
                                           faltam)]
    return []


def main():
    if not PISO.exists():
        print('  ⏳ o arquivo do piso nao esta neste disco'); return 0
    r = confere()
    for x in r:
        print('  ⛔ %s' % x)
    if not r:
        piso, cand = conjuntos()
        print('  ✅ os dois grupos de %d diferem em %s x %s, e o corpo declara a diferenca'
              % (len(piso), sorted(piso - cand) or '-', sorted(cand - piso) or '-'))
    return 1 if r else 0


def autoteste():
    mal = 0
    n = len(confere())
    print(f"  {'✅' if n == 0 else '⛔'} corpo atual: {n} problema(s), esperado 0")
    mal += n != 0
    # ⛔ o defeito real replantado: a frase que declara a diferenca some
    t = _texto()
    doente = re.sub(r'ARNIQA', 'a further model', t)
    n = len(confere(doente))
    print(f"  {'✅' if n == 1 else '⛔'} sem a frase da diferenca: {n}, esperado 1")
    mal += n != 1
    # ⚠️ e a perna que separa: se os conjuntos fossem IGUAIS, nada a exigir
    piso, cand = conjuntos()
    print(f"  {'✅' if piso != cand else '⛔'} os dois grupos de fato diferem "
          f"({sorted(piso - cand)} x {sorted(cand - piso)}), entao a regra e exercitada")
    mal += piso == cand
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
