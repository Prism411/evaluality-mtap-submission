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
QB = Path('/data/projects/benchmark')
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
        # ⚠️ 28/09: a tabela passou a ter tres colunas (Method, Opinion training, Pol.)
        if len(c) < 3:
            continue
        nome = re.sub(r'~?\\citep\{[^}]*\}|\$|\\', '', c[0]).strip()
        POREXT = {'KonIQ-10k': 'KQ', 'LIVE': 'LV', 'none': 'OU',
                  'multi-database mixture': 'Mix'}
        # ⚠️ a citacao sai da coluna de TREINO tambem, nao so do nome: desde
        # que a LIVE ganhou referencia propria, `LIVE~\\citep{...}` nao casava
        # com `LV` e a guarda reprovava por formatacao, nao por fato.
        treino = re.sub(r'~?\\citep\{[^}]*\}', '', c[1]).strip()
        cod = POREXT.get(treino, treino)
        if cod in ('--', '---', ''):
            continue
        for um in nome.split(';'):
            um = um.strip()
            if um:
                out[um] = cod
    return out


# as tres bases em que os metodos sao AVALIADOS. A LIVE de 2006, em que o
# checkpoint do BRISQUE foi treinado, nao esta entre elas -- e essa distincao
# que decide se ela conta como vista.
AVALIADAS = ('KADID-10k', 'KonIQ-10k', 'LIVE In the Wild')
# de que base cada codigo de treino sai, quando ela e uma das avaliadas
TREINO_AVALIADA = {'KQ': 'KonIQ-10k', 'LV': None, 'OU': None}


def unseen_da_tabela(texto=None):
    """O que a coluna `Unseen databases` imprime, por metodo."""
    t = texto if texto is not None else (AQUI / 'sec_method.tex').read_text(encoding='utf-8')
    i = t.find('\\label{tab:methods}')
    ini, fim = t.rfind('\\begin{table}', 0, i), t.find('\\end{table}', i)
    out = {}
    for linha in t[ini:fim].split('\n'):
        if ' & ' not in linha or '\\hd{' in linha or '\\multicolumn' in linha:
            continue
        c = [x.strip() for x in re.sub(r'\\rowcolor\{[^}]*\}', '', linha).split('&')]
        if len(c) < 5:
            continue
        nome = re.sub(r'~?\\citep\{[^}]*\}|\$|\\', '', c[0]).strip()
        if nome:
            out[nome] = [x.strip() for x in c[2].split(',') if x.strip() not in ('---', '')]
    return out


def unseen_confere(texto=None):
    """⛔ A COLUNA DERIVADA. Ate 27/09 a guarda conferia so a coluna de TREINO,
    que alimenta esta -- e o erro morava na derivada: a linha do BRISQUE omitia
    a LIVE In the Wild porque quem montou a tabela leu «LIVE» como sendo a
    mesma base. Sao duas: a LIVE de 2006 treinou o checkpoint e NAO e avaliada
    aqui, entao as tres avaliadas sao nao vistas para ele.
    ⚠️ Guarda que confere so a coluna de entrada aprova a conta errada feita
    com a entrada certa.
    """
    if not FONTE.exists():
        return []
    t = texto if texto is not None else (AQUI / 'sec_method.tex').read_text(encoding='utf-8')
    if 'Unseen databases' not in t:
        # ⭐ 28/09 (parecer): a coluna derivada saiu da Tabela 2 e a regra foi para a legenda.
        # Sem coluna nao ha conta errada a conferir; o que tem de estar escrito e a REGRA, e o
        # caso que ja enganou uma vez (a LIVE do BRISQUE nao e a LIVE In the Wild).
        falta = [p for p in (r'absent from that\s+training', r'LIVE database of the BRISQUE')
                 if not re.search(p, t)]
        return ['a legenda da Tabela 2 nao diz mais a regra das nao vistas: falta %s' % falta] if falta else []
    d = json.load(open(FONTE))
    tab, impresso = da_tabela(texto), unseen_da_tabela(texto)
    ruins = []
    for nome, cod in tab.items():
        if nome not in d['por_modelo'] or cod not in TREINO_AVALIADA:
            continue
        vista = TREINO_AVALIADA[cod]
        esperado = [b for b in AVALIADAS if b != vista]
        obtido = impresso.get(nome, [])
        if sorted(obtido) != sorted(esperado):
            ruins.append('%s treina em %s, entao nao vistas = %s; a tabela imprime %s'
                         % (nome, cod, esperado, obtido))
    return ruins


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
    ruins += unseen_confere(texto)
    return not ruins, ruins, len(d['por_modelo'])


def sem_verificacao(texto=None):
    """⏳ Codigos impressos na Tabela 2 que NUNCA foram conferidos contra o codigo.

    ⛔ Ate 25/09 a guarda contava so quem estava no arquivo, entao quem faltava passava em
    silencio. O denominador certo e a TABELA.
    """
    if not FONTE.exists():
        return []
    d = json.load(open(FONTE))
    return sorted(set(da_tabela(texto)) - set(d['por_modelo']))


def _autoteste():
    ok, r, n = confere()
    assert ok, '⛔ ja ha desacordo: %s' % r[:2]
    assert n >= 10, '⛔ so %d modelos conferidos: aprovaria no vacuo' % n
    t = (AQUI / 'sec_method.tex').read_text(encoding='utf-8')
    sujo = t.replace('LIQE & vision--language', 'LIQE & vision--language', 1)
    sujo = re.sub(r'(LIQE\s*&\s*)KonIQ-10k(\s*&)', r'\1none\2', t, count=1)
    assert sujo != t, '⛔ nao consegui montar o mundo errado'
    assert not confere(texto=sujo)[0], '⛔ NAO separa: o codigo de supervisao trocado passou'
    # ⛔ e a perna de 27/09, na redacao HISTORICA: a linha do BRISQUE sem a
    # LIVE In the Wild. Era assim que a tabela estava, e a guarda aprovava.
    # ⚠️ 28/09: sem a coluna derivada, o defeito historico passa a ser a LEGENDA perder a
    # frase que separa a LIVE do BRISQUE da LIVE In the Wild.
    velho = re.sub(r'the LIVE database of the BRISQUE\s+checkpoint is not among them, so all three are unseen for it\. ',
                   '', t, count=1)
    assert velho != t, '⛔ nao consegui montar a legenda historica do BRISQUE'
    assert not confere(texto=velho)[0], (
        '⛔ NAO separa: a linha do BRISQUE sem a LIVE In the Wild passou')
    print('  autoteste ✅ (codigo do LIQE trocado REPROVA; e a linha historica '
          'do BRISQUE, sem a LIVE In the Wild, tambem)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins, n = confere()
    print('  %d codigos de supervisao conferidos contra o pyiqa e as fontes' % n)
    _falta = sem_verificacao()
    if _falta:
        print('  ⏳ AGUARDA VERIFICACAO: %d codigo(s) da Tabela 2 nunca conferidos contra '
              'o checkpoint que roda: %s' % (len(_falta), ', '.join(_falta)))
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
