#!/usr/bin/env python3
"""⛔ O «DE ONZE TRABALHOS-FONTE» FECHA COM O QUE O LEITOR CONSEGUE CONTAR?

POR QUE EXISTE (08/09/2026). O artigo diz «sixteen operations reimplemented from eleven
source works» em tres lugares, e a decima-primeira — `xu2024property` — **so aparecia numa
tabela do suplementar**. Um leitor que conte as citacoes do corpo acha DEZ, e conclui que a
contagem esta errada quando ela nao esta.

⚠️ Isso nao e o mesmo problema de bibliografia orfa: a entrada E citada, so que fora do
corpo. E tambem nao e o mesmo que a auditoria documental, que cobre os DEZ trabalhos de
sumarizacao — o Xu entra pela proveniencia de uma operacao, nao pela leitura de validacao.

A guarda amarra as duas pontas: o numero por extenso que o corpo imprime tem de bater com
os trabalhos que a proveniencia atribui as operacoes, e cada um deles tem de aparecer citado
em algum lugar do artigo.

Autoteste de duas pernas: o estado atual passa, e tirar uma citacao REPROVA.
"""
import io
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
QB = Path('/data/projects/benchmark')
CORPO = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex', 'sec_results.tex',
         'sec_discussion.tex', 'sec_conclusion.tex']
POREXT = {8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve', 13: 'thirteen'}


def trabalhos_da_fonte():
    p = json.load(open(QB / 'proveniencia_das_operacoes.json'))
    usados = set()
    for op in p['as_15_da_tabela_S3']:
        v = p['proveniencia'].get(op)
        if isinstance(v, str):
            usados.add(v)
        elif isinstance(v, list):
            usados |= set(v)
    return usados


def citadas(textos=None):
    t = textos if textos is not None else ' '.join(
        (AQUI / f).read_text(encoding='utf-8') for f in CORPO)
    out = set()
    for c in re.findall(r'\\cite[pt]?\*?(?:\[[^\]]*\])*\{([^}]*)\}', t):
        out |= {x.strip() for x in c.split(',') if x.strip()}
    return out


def confere(textos=None):
    usados = trabalhos_da_fonte()
    n = len(usados)
    t = textos if textos is not None else ' '.join(
        (AQUI / f).read_text(encoding='utf-8') for f in CORPO)
    ruins = []
    # 1. o numero por extenso que o corpo imprime
    palavra = POREXT.get(n)
    if palavra and not re.search(r'(?:from|\\fontesTrabalhos\{\}) %s source works|'
                                 r'\\fontesTrabalhos\{\} source works' % palavra, t):
        achado = re.search(r'from (\w+) source works', t)
        ruins.append('a proveniencia tem %d trabalhos e o corpo diz %r'
                     % (n, achado.group(1) if achado else '(nada)'))
    # ⛔ BURACO MEDIDO EM 08/09 por `mutacao_da_suite.py`: exigir que a frase CERTA apareca
    # nao impede a ERRADA de aparecer ao lado. Trocar «\fontesTrabalhos{} source works» por
    # «nine source works» num dos tres lugares passava, porque os outros dois seguravam a
    # checagem. Agora TODA ocorrencia tem de trazer o numero certo ou a macro.
    # ⚠️ so a forma do INVENTARIO, «from N source works». «the ten source works read in
    # full» e outra contagem, legitima, e acusar ela seria acusar em massa — sinal de
    # verificador errado, nao de defeito.
    for m in re.finditer(r'from\s+(\S+)\s+source works', t):
        tok = m.group(1)
        if tok.startswith('\\fontesTrabalhos'):
            continue
        digitos = re.findall(r'\d+', tok)          # «from \textbf{11} source works»
        if digitos and int(digitos[0]) == n:
            continue
        if palavra and tok.lower() != palavra:
            ruins.append('«from %s source works» no corpo, e a proveniencia tem %d'
                         % (tok, n))
    # 2. cada um deles citado no corpo
    cit = citadas(t)
    fora = sorted(usados - cit)
    if fora:
        ruins.append('atribuido a uma operacao mas nao citado no corpo: %s' % ', '.join(fora))
    return not ruins, ruins, n


def _autoteste():
    ok, r, n = confere()
    assert ok, '⛔ ja ha desacordo: %s' % r
    assert n >= 8, '⛔ so %d trabalhos: aprovaria no vacuo' % n
    t = ' '.join((AQUI / f).read_text(encoding='utf-8') for f in CORPO)
    alvo = sorted(trabalhos_da_fonte())[0]
    sujo = t.replace('\\citep{%s}' % alvo, '').replace('\\citet{%s}' % alvo, '')
    sujo = re.sub(r'\\cite[pt]?\{([^}]*)' + re.escape(alvo) + r',?\s*', r'\\citep{\1', sujo)
    assert sujo != t, '⛔ nao consegui montar o mundo errado'
    assert not confere(textos=sujo)[0], '⛔ NAO separa: fonte nao citada passou'
    print('  autoteste ✅ (tirando a citacao de um trabalho-fonte, REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins, n = confere()
    print('  %d trabalhos-fonte na proveniencia, todos citados no corpo' % n
          if ok else '  %d trabalhos-fonte' % n)
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
