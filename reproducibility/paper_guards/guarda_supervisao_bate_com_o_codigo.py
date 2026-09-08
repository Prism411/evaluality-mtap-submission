#!/usr/bin/env python3
"""⛔ A COLUNA `Sup.` DA TABELA 1 BATE COM O CHECKPOINT QUE O CODIGO CARREGA?

POR QUE EXISTE (08/09/2026). A regra de generalizacao le «a menor correlacao em TODA base em
que o metodo nao foi ajustado». Se um checkpoint estiver atribuido a base errada, muda quais
bases contam como NAO VISTAS e portanto muda quem passa na triagem. Nada conferia isso: a
coluna vinha da leitura de quem montou a tabela.

⚠️ E ha uma distincao que so aparece quando se olha: o ARTIGO de cada modelo diz em que os
AUTORES treinaram; a coluna afirma qual CHECKPOINT LIBERADO foi usado. O LIQE, por exemplo,
foi treinado no KADID-10k E no KonIQ-10k separadamente, e o que decide o veredito e qual
deles o `pyiqa` carrega. **A fonte certa e o codigo que roda, nao o artigo.**

Autoteste de duas pernas: a tabela atual passa, e um codigo trocado REPROVA.
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
QB = Path('/dados/Projetos/quality-benchmark')
FONTE = QB / 'o_que_as_fontes_dizem_do_treino.json'


def da_tabela(texto=None):
    """O que a Tabela 1 do artigo imprime na coluna `Sup.`, por metodo."""
    t = texto if texto is not None else (AQUI / 'sec_method.tex').read_text(encoding='utf-8')
    i = t.find('\\label{tab:methods}')
    if i < 0:
        return {}
    ini, fim = t.rfind('\\begin{table}', 0, i), t.find('\\end{table}', i)
    out = {}
    for linha in t[ini:fim].split('\n'):
        if ' & ' not in linha or '\\hd{' in linha:
            continue
        c = [x.strip() for x in re.sub(r'\\rowcolor\{[^}]*\}', '', linha).split('&')]
        if len(c) < 7:
            continue
        nome = re.sub(r'~?\\citep\{[^}]*\}|\$|\\', '', c[0]).strip()
        out[nome] = c[3].strip()
    return out


def confere(texto=None):
    if not FONTE.exists():
        return False, ['%s nao existe: rodar o script que o produz' % FONTE.name], 0
    d = json.load(open(FONTE))
    tab = da_tabela(texto)
    ruins = []
    for nome, v in d['por_modelo'].items():
        if not v['confere']:
            ruins.append('%s: o codigo carrega %r, incompativel com %s'
                         % (nome, v['checkpoint_ou_evidencia'], v['codigo_na_tabela']))
        # e o que a tabela IMPRIME hoje tem de ser o que foi conferido
        impresso = tab.get(nome)
        if impresso is not None and impresso != v['codigo_na_tabela']:
            ruins.append('%s: a tabela imprime %r, e o conferido foi %r'
                         % (nome, impresso, v['codigo_na_tabela']))
    return not ruins, ruins, len(d['por_modelo'])


def _autoteste():
    ok, r, n = confere()
    assert ok, '⛔ ja ha desacordo: %s' % r[:2]
    assert n >= 10, '⛔ so %d modelos conferidos: aprovaria no vacuo' % n
    t = (AQUI / 'sec_method.tex').read_text(encoding='utf-8')
    sujo = t.replace('LIQE & vision--language', 'LIQE & vision--language', 1)
    sujo = re.sub(r'(LIQE[^\n]*?&[^&]*&[^&]*&\s*)KQ(\s*&)', r'\1OU\2', t, count=1)
    assert sujo != t, '⛔ nao consegui montar o mundo errado'
    assert not confere(texto=sujo)[0], '⛔ NAO separa: o codigo de supervisao trocado passou'
    print('  autoteste ✅ (com o codigo do LIQE trocado para OU, REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins, n = confere()
    print('  %d codigos de supervisao conferidos contra o pyiqa e as fontes' % n)
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
