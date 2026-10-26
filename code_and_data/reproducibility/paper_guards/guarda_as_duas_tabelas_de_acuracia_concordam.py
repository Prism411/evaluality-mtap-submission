#!/usr/bin/env python3
r"""⛔ A TABELA 6 E A S32 DAO A MESMA ACURACIA PARA A MESMA OPERACAO?

POR QUE EXISTE (25/09/2026, parecer v9, §1.1). O revisor comparou as duas tabelas e
achou acuracias diferentes para as mesmas operacoes sobre os mesmos 800 pares — Gygli
83,8 contra 67,5, Srinivas 87,0 contra 74,5 — e tratou como BLOQUEIO de submissao.

🔴 Estava certo. Nao eram duas rodadas: as acuracias POR TIPO sao identicas. Eram duas
AGREGACOES da mesma medicao, e a S32 publicava a nao canonica sob a legenda da canonica.
Nenhuma das 48 guardas via: cada tabela conferia contra a PROPRIA fonte, e as duas fontes
existiam, estavam certas e mediam coisas diferentes.

⭐ AS DUAS CHECAGENS, e as duas sao decisivas:
  1. na Tabela 6, a media impressa e a media das OITO celulas impressas ao lado dela.
     Isso fixa a regua canonica NA PROPRIA PAGINA, sem depender de arquivo nenhum;
  2. toda acuracia da S32 casa com a media de alguma linha da Tabela 6.

⚠️ As duas operacoes de SEQUENCIA nao estao na Tabela 6 (a regra de quadro isolado as
exclui), entao ficam isentas da checagem 2 — e a isencao e por NOME, declarada aqui, nao
por «nao achei, deixa passar».

Autoteste de tres pernas: o estado atual passa; mexer numa media da Tabela 6 reprova; e
pôr de volta o VALOR HISTORICO errado da S32 (Gygli 67,5) reprova.
"""
import re
import sys
from pathlib import Path

A = Path(__file__).parent
SINTESE, DEZ = A / 'tab_sintese.tex', A / 'tab_dezessete.tex'
# ⚠️ as unicas linhas da S32 que a Tabela 6 nao tem: operacoes de sequencia
ISENTAS = {'sobel\\_cv', 'qaroush\\_movimento'}
TOL = 0.06


def medias_da_tabela6(txt):
    """(oito celulas, media impressa) por linha, lidas do .tex publicado."""
    out = []
    for l in txt.splitlines():
        if not l.strip().endswith(r'\\') or 'cellcolor' not in l:
            continue
        cels = [int(m.group(1)) for m in
                re.finditer(r'\\cellcolor\{[^}]*\}(?:\\textcolor\{[^}]*\}\{)?'
                            r'(?:\\itshape )?\s*(\d+)', l)]
        m = re.search(r'\\textbf\{(\d+\.\d)\}', l)
        if len(cels) == 8 and m:
            out.append((cels, float(m.group(1))))
    return out


def acuracias_da_s32(txt):
    """(identificador, acuracia canonica) por linha."""
    out = []
    for l in txt.splitlines():
        m = re.match(r'\\rowcolor\{[^}]*\}\\texttt\{((?:[^{}]|\\allowbreak\{\})*)\}'
                     r'(?:\$\^\{\\ddagger\}\$)? & [^&]* & (\d+\.\d) &', l)
        if m:
            out.append((m.group(1).replace(r'\allowbreak{}', ''), float(m.group(2))))
    return out


def confere(t6, s32):
    ruins = []
    linhas = medias_da_tabela6(t6)
    if len(linhas) < 10:
        ruins.append(('tab_sintese.tex', '⛔ li so %d linhas com oito celulas: o formato '
                                         'da tabela mudou e a guarda parou de ver' % len(linhas)))
        return ruins
    for cels, med in linhas:
        calc = sum(cels) / 8
        if abs(calc - med) > TOL:
            ruins.append(('tab_sintese.tex',
                          'media impressa %.1f, media das oito celulas %.2f (%s)'
                          % (med, calc, cels)))
    medias = [m for _, m in linhas]
    op = acuracias_da_s32(s32)
    if len(op) != 17:
        ruins.append(('tab_dezessete.tex', '⛔ li %d linhas em vez de 17' % len(op)))
    for nome, acc in op:
        if nome in ISENTAS:
            continue
        if not any(abs(acc - m) <= TOL for m in medias):
            ruins.append(('tab_dezessete.tex',
                          '%s tem %.1f, que nao casa com media nenhuma da Tabela 6'
                          % (nome, acc)))
    return ruins


def _autoteste():
    t6, s32 = SINTESE.read_text(), DEZ.read_text()
    if confere(t6, s32):
        return False, '⛔ o estado atual ja reprova: %s' % confere(t6, s32)[:1]
    mau6 = re.sub(r'\\textbf\{83\.8\}', r'\\textbf{81.8}', t6, count=1)
    if mau6 == t6:
        return False, ('⛔ controle morto: nao achei a media 83.8 na Tabela 6 para '
                       'perturbar; o formato mudou')
    if not confere(mau6, s32):
        return False, '⛔ media adulterada na Tabela 6 passou'
    # o valor HISTORICO do defeito, nao um numero qualquer
    mauS = re.sub(r'(\\texttt\{gygli.{0,20}?media.{0,20}?crua\}[^&]*&[^&]*& )83\.8',
                  r'\g<1>67.5', s32, count=1)
    if mauS == s32:
        return False, ('⛔ controle morto: nao achei a linha do Gygli na S32 para plantar '
                       'o valor historico 67,5')
    if not confere(t6, mauS):
        return False, '⛔ o valor HISTORICO errado (Gygli 67,5) passou'
    return True, ''


if __name__ == '__main__':
    ok, msg = _autoteste()
    assert ok, msg
    print('  autoteste ✅ (media adulterada e o Gygli 67,5 historico REPROVAM)')
    ruins = confere(SINTESE.read_text(), DEZ.read_text())
    for f, m in ruins:
        print('  ⛔ %s: %s' % (f, m))
    if ruins:
        print('  ⛔ as duas tabelas de acuracia discordam')
        sys.exit(1)
    print('  ✅ Tabela 6 e S32 dao a mesma acuracia, e a media da Tabela 6 fecha na pagina')
