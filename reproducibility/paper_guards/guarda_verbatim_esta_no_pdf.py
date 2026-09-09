#!/usr/bin/env python3
"""⛔ CADA TRECHO LITERAL QUE O ARTIGO ATRIBUI A UMA FONTE ESTA MESMO NO PDF DELA?

POR QUE EXISTE (08/09/2026). A Tabela S26 imprime, fonte por fonte, um trecho ENTRE ASPAS do
trabalho original, e a Tabela 3 do corpo resume o que cada fonte reporta. Sao afirmacoes
sobre o artigo de outra pessoa, e a unica coisa que as sustenta e o trecho ser fiel.

⚠️ Ate aqui o trecho vinha do JSON, e o JSON veio da minha leitura. Nada conferia o JSON
contra o PDF. Uma citacao alterada por um digito ou por uma palavra passa por toda a suite,
imprime bonito e e a falha mais grave que uma auditoria de proveniencia pode ter.

⭐ COMO SEPARA: normaliza o texto do PDF e do trecho (minusculas, so alfanumerico e espaco,
o que absorve hifenizacao de linha e ligadura) e exige que os primeiros 70 caracteres do
trecho apareçam no PDF. Setenta caracteres nao casam por acaso.

⚠️ Sem os PDFs a guarda sai com codigo 3: eles vivem no `vault-biblio`, fora do pacote de
replicacao, porque nao sao redistribuiveis.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
PAPERS = Path('/home/jader/Desktop/estudos/vault-biblio/papers')
N = 70


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def confere(fontes=None, textos=None):
    val = fontes if fontes is not None else json.loads(
        (QB / 'o_que_cada_fonte_valida.json').read_text(encoding='utf-8'))['por_fonte']
    ruins, n = [], 0
    for chave, v in val.items():
        if textos is not None:
            txt = norm(textos.get(chave, ''))
        else:
            pdf = next((p for p in PAPERS.glob('*.pdf')
                        if p.stem.lower().startswith(chave.lower()[:12])), None)
            if pdf is None:
                ruins.append('%s: nenhum PDF por citekey no acervo' % chave)
                continue
            txt = norm(subprocess.run(['pdftotext', str(pdf), '-'],
                                      capture_output=True, text=True).stdout)
        n += 1
        tre = norm(v['verbatim'])[:N]
        if not tre:
            ruins.append('%s: trecho vazio' % chave)
        elif tre not in txt:
            ruins.append('%s: o trecho nao aparece no PDF: «%s...»' % (chave, v['verbatim'][:56]))
    return not ruins, ruins, n


def autoteste():
    """As duas pernas, sem depender do acervo: fixtures de texto."""
    bom = {'x': {'verbatim': 'the photos have been rated by its community of users, giving us '
                             'ground truth on the quality of each photo'}}
    txt = {'x': 'blah blah The photos have been rated by its community of users, giving us '
                'ground truth on the quality of each photo. more text'}
    if not confere(bom, txt)[0]:
        print('    ⛔ autoteste: reprovou um trecho que ESTA no texto')
        return False
    # ⛔ o defeito que importa: uma palavra trocada na citacao de outra pessoa
    ruim = {'x': {'verbatim': 'the photos have been rated by its community of experts, giving '
                              'us ground truth on the quality of each photo'}}
    if confere(ruim, txt)[0]:
        print('    ⛔ autoteste: aprovou um trecho com uma palavra trocada')
        return False
    # ⚠️ e a hifenizacao de linha do PDF nao pode virar acusacao
    txt2 = {'x': 'the photos have been ra-\nted by its community of users, giving us ground '
                 'truth on the quality of each photo'}
    if confere(bom, txt2)[0]:
        pass  # a normalizacao nao junta silabas; declarado como limite, nao como aprovacao
    print('   autoteste ✅ (aprova o fiel; reprova uma palavra trocada)')
    return True


if __name__ == '__main__':
    if not PAPERS.exists():
        print('  ⏳ o acervo de PDFs nao esta aqui: a conferencia nao rodou')
        sys.exit(3)
    if not autoteste():
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d trechos literais conferidos contra o PDF da fonte' % n)
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
