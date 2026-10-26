#!/usr/bin/env python3
"""⛔ NENHUMA CELULA DA MATRIZ DE COBERTURA PODE FALTAR POR HISTORIA DE IMPLEMENTACAO.

POR QUE EXISTE (21/09/2026). Ate hoje a Tabela de cobertura declarava, na propria legenda,
que seis operacoes nao tinham resultado a jusante «porque entraram depois que a passada
rodou». O [co-author] leu o artigo e concluiu, duas vezes, que a metodologia se aplicava
a um trabalho so. A leitura dele era correta e a legenda dizia por que.

A REGRA QUE ESTA GUARDA IMPOE. Ou a operacao entra no eixo, ou a ausencia tem motivo de
PRINCIPIO, isto e, uma propriedade da FONTE e nao da nossa ordem de trabalho. Hoje o unico
motivo de principio aceito e o do `si`: a fonte nao declara direcao, entao escolher o maior
valor seria arbitrario.

⚠️ E a guarda confere o TEXTO e o DADO, porque os dois podem discordar:
  1. a legenda da tabela nao pode conter nenhuma expressao de historia de implementacao;
  2. nenhuma celula «Absent because» pode trazer motivo que nao seja o de principio;
  3. as contagens impressas na ultima linha tem de bater com os JSON de origem.

⭐ AUTOTESTE DE DUAS PERNAS (`--autoteste`): a guarda tem de PASSAR no mundo certo e
REPROVAR no errado. Uma guarda que nao reprova nada e o defeito, nao o teste.
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from caminho_dos_dados import DADOS as QB   # noqa: E402

TABELA = AQUI / 'tab_cobertura.tex'

# expressoes que denunciam ausencia por ordem de trabalho, e nao por propriedade da fonte
HISTORIA = [
    r'after the downstream pass',
    r'added to the implementation',
    r'sequence of (?:our )?work',
    r'not yet (?:run|measured|computed)',
    r'stated next step',
    r'a property of our',
]

# o unico motivo de principio aceito hoje, e ele nomeia uma propriedade da FONTE
PRINCIPIO = re.compile(r'source declares no direction', re.I)


def celulas_absent(tex):
    """o conteudo de cada celula «Absent because», que e a ultima de cada linha"""
    out = []
    for linha in tex.splitlines():
        m = re.search(r'\\textcolor\{black!55\}\{\\scriptsize ([^}]*)\}', linha)
        if m:
            out.append(m.group(1).strip())
    return out


def confere(tex, dados=True):
    """devolve a lista de falhas; vazia significa aprovado"""
    falhas = []

    # --- 1. a legenda nao pode falar de ordem de trabalho ---
    mc = re.search(r'\\caption\{(.*?)\}\s*\n\s*\\label', tex, re.S)
    legenda = mc.group(1) if mc else tex
    for rx in HISTORIA:
        for m in re.finditer(rx, legenda, re.I):
            # ⛔ A PRIMEIRA VERSAO DESTA GUARDA REPROVOU A LEGENDA CERTA. Ela dizia
            # «a property of the source, NOT OF OUR SEQUENCE OF WORK», que e a NEGACAO
            # do defeito, e o padrao disparou na negacao. Declarar que o defeito nao
            # existe e o oposto de te-lo, e uma guarda que nao distingue os dois obriga
            # o texto a nunca nomear o problema que resolveu.
            antes = legenda[max(0, m.start() - 60):m.start()].lower()
            if re.search(r'\b(not|never|rather than|instead of|no longer)\b[^.]*$', antes):
                continue
            falhas.append(f'legenda contem motivo de historia de implementacao: /{rx}/ '
                          f'em «...{legenda[max(0, m.start()-40):m.end()+20].strip()}...»')

    # --- 2. nenhuma celula pode trazer motivo que nao seja o de principio ---
    for c in celulas_absent(tex):
        if not c:
            continue
        if not PRINCIPIO.search(c):
            falhas.append(f'celula «Absent because» com motivo nao-principiado: «{c}»')

    if not dados:
        return falhas

    # --- 3. as contagens impressas batem com os JSON de origem ---
    m = re.search(r'\\textbf\{of (\d+)\}((?:\s*&\s*\\textbf\{\d+\})+)', tex)
    if not m:
        falhas.append('nao achei a linha de contagens da tabela')
        return falhas
    total = int(m.group(1))
    impressas = [int(x) for x in re.findall(r'\\textbf\{(\d+)\}', m.group(2))]
    if len(impressas) != 5:
        falhas.append(f'esperava 5 contagens, achei {len(impressas)}')
        return falhas
    _, _, _, pis_imp, jus_imp = impressas

    auditadas = set(json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao'])
    piso = set(json.load(open(QB / 'o_piso_numa_bancada_so.json'))['por_operacao'])
    jus = {x['nome'] for x in json.load(open(QB / 'jusante_lado_a_lado.json'))['linhas']
           if 'sumarizacao' in x['familia']}
    jus |= set(json.load(open(
        QB / 'jusante_ops_faltantes_caminho_velho.json'))['concordancia_com_sift'])

    if total != len(auditadas):
        falhas.append(f'a tabela diz «of {total}» e o inventario tem {len(auditadas)}')
    if pis_imp != len(auditadas & piso):
        falhas.append(f'Floor impresso {pis_imp}, JSON da {len(auditadas & piso)}')
    if jus_imp != len(auditadas & jus):
        falhas.append(f'Down. impresso {jus_imp}, JSON da {len(auditadas & jus)}')

    # --- 4. o que falta em cada eixo tem de ser SO o motivo de principio ---
    sem_piso = auditadas - piso
    sem_jus = auditadas - jus
    for eixo, faltantes in (('Floor', sem_piso), ('Down.', sem_jus)):
        indevidos = faltantes - {'si', 'spatial_information'}
        if indevidos:
            falhas.append(f'{eixo}: operacoes ausentes sem motivo de principio: '
                          f'{sorted(indevidos)}')
    return falhas


def autoteste():
    """perna A: passa no texto real. perna B: REPROVA no texto com o defeito de volta."""
    tex = TABELA.read_text(encoding='utf-8')
    erros = []

    a = confere(tex)
    if a:
        erros.append(f'perna A (mundo certo) devia passar e reprovou: {a}')

    # o defeito real, tal como estava ate 21/09: a legenda explicando a ausencia pela
    # ordem de trabalho, e uma celula dizendo o mesmo
    # ⚠️ o texto injetado e AFIRMATIVO, sem negacao antes, que e o defeito real tal
    # como estava ate 21/09. Se a guarda deixar isto passar, ela nao serve.
    ruim = tex.replace(
        'Sensitivity and generalization cover all',
        'The other six operations without a downstream result were added to the '
        'implementation after the downstream pass was run, which is a property of our '
        'sequence of work. '
        'Sensitivity and generalization cover all', 1)
    b = confere(ruim, dados=False)
    if not b:
        erros.append('perna B (defeito de volta) devia REPROVAR e passou')

    ruim2 = tex.replace(
        r'\textcolor{black!55}{\scriptsize }',
        r'\textcolor{black!55}{\scriptsize after the downstream pass}', 1)
    c = confere(ruim2, dados=False)
    if not c:
        erros.append('perna B2 (celula com motivo de ordem de trabalho) devia REPROVAR')

    # perna C: a excecao de negacao nao pode virar porta dos fundos. Uma frase que
    # NEGA num ponto e AFIRMA noutro tem de reprovar pela afirmacao.
    ruim3 = tex.replace(
        'Sensitivity and generalization cover all',
        'This is not a property of our sequence of work. Six operations were added to '
        'the implementation after the downstream pass was run. '
        'Sensitivity and generalization cover all', 1)
    d = confere(ruim3, dados=False)
    if not d:
        erros.append('perna C (nega e depois afirma) devia REPROVAR pela afirmacao')

    return erros


def main():
    if '--autoteste' in sys.argv:
        erros = autoteste()
        for e in erros:
            print(f'  🔴 {e}')
        print('✅ autoteste de duas pernas: passa no certo e reprova no errado'
              if not erros else '🔴 AUTOTESTE FALHOU')
        return 1 if erros else 0

    falhas = confere(TABELA.read_text(encoding='utf-8'))
    for f in falhas:
        print(f'  🔴 {f}')
    print('✅ cobertura sem buraco de implementacao' if not falhas
          else f'🔴 {len(falhas)} falha(s)')
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
