#!/usr/bin/env python3
"""⛔ AS TABELAS FECHAM COM ELAS MESMAS?

POR QUE EXISTE (08/09/2026). O metodo afirma que «every value in the tables and figures of
this article is generated from the measurement files it points to, with the supplementary
tables transcribed from the same files». **Dezoito tabelas do suplementar sao escritas a
mao**, e nada conferia essa transcricao.

⭐ NAO da para conferir cada uma contra a fonte sem reescrever os dezoito geradores. Mas da
para conferir a ARITMETICA INTERNA, que e barata e discrimina: quando uma tabela traz
«9/15 (60,0 %)» e um kappa ao lado, os tres numeros estao amarrados. Um erro de transcricao
quebra a relacao; uma transcricao correta a preserva.

Duas relacoes conferidas:
  1. todo par «n/N (pct %)» — a porcentagem e n/N;
  2. o kappa de concordancia — $(p_o - p_e)/(1 - p_e)$, com o $p_e$ que a propria legenda
     declara.

Autoteste de duas pernas: os valores atuais passam, e um digito trocado REPROVA.
"""
import glob
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
PAR = re.compile(r'(\d+)\s*/\s*(\d+)\s*(?:\\[,;: ]|~|\s)*\(\s*([\d.]+)\s*\\?%')
LINHA_K = re.compile(r'(\d+)/(\d+)\s*\\?[,; ]*\(([\d.]+)\\%\)\}\s*&\s*\\pf[A-D]\{\$([+-][\d.]+)\$')
# ⚠️ o ponto vem envolto em `\pfA{...}`, entao o padrao tem de atravessar o comando
IC = re.compile(r'(?:\\pf[A-Z]\{|\$)?\s*([+-]?\d*\.?\d+)\s*\}?\s*(?:\\%)?\s*&\s*'
                r'\$?\s*\[\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*\]')


def arquivos():
    return (['supplementary.tex'] + sorted(p.name for p in AQUI.glob('tab_*.tex'))
            + sorted(p.name for p in AQUI.glob('fig_*.tex')))


def plano(txt):
    return re.sub(r'\s+', ' ', re.sub(r'(?m)^\s*%.*$', '', txt))


def confere(fontes=None):
    fontes = fontes or {f: (AQUI / f).read_text(encoding='utf-8')
                        for f in arquivos() if (AQUI / f).exists()}
    ruins, n_par, n_k, n_ic = [], 0, 0, [0]
    for nome, txt in fontes.items():
        t = plano(txt)
        for m in PAR.finditer(t):
            a, b, pct = int(m.group(1)), int(m.group(2)), float(m.group(3))
            n_par += 1
            if b and abs(round(100 * a / b, 1) - pct) > 0.06:
                ruins.append('%s: %d/%d dito %.1f %%, e %.1f %%'
                             % (nome, a, b, pct, 100 * a / b))
        # o kappa, quando a legenda declara o p_e
        for mpe in re.finditer(r'p\}_e\}? *= *([0-9.]+)', t):
            pe = float(mpe.group(1))
            trecho = t[mpe.end():mpe.end() + 4000]
            for m in LINHA_K.finditer(trecho):
                a, b, _p, k = int(m.group(1)), int(m.group(2)), m.group(3), float(m.group(4))
                n_k += 1
                k_c = (a / b - pe) / (1 - pe)
                if abs(k_c - k) > 0.0016:
                    ruins.append('%s: %d/%d com p_e=%.3f da kappa %.3f, e %.3f'
                                 % (nome, a, b, pe, k, k_c))
        # 3. o ponto estimado tem de cair DENTRO do seu proprio intervalo
        for m in IC.finditer(t):
            p, lo, hi = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
            n_ic[0] += 1
            if lo > hi:
                ruins.append('%s: intervalo invertido [%s, %s]' % (nome, lo, hi))
            elif not (lo - 1e-9 <= p <= hi + 1e-9):
                ruins.append('%s: ponto %s fora de [%s, %s]' % (nome, p, lo, hi))
    return not ruins, ruins, n_par, n_k, n_ic[0]


def _autoteste():
    ok, r, np_, nk, nic = confere()
    assert ok, '⛔ ja ha desacordo: %s' % r[:2]
    assert np_ >= 10, '⛔ so %d pares lidos: aprovaria no vacuo' % np_
    BOM = {'x.tex': r'the rule holds on 9/15 \ (60.0\%) of the clusters here.'}
    RUIM = {'x.tex': r'the rule holds on 9/15 \ (66.7\%) of the clusters here.'}
    assert confere(BOM)[0], '⛔ reprovou uma porcentagem correta'
    assert not confere(RUIM)[0], '⛔ NAO separa: 9/15 dito como 66,7 %% passou'
    IC_BOM = {'x.tex': r'\pfA{0.807} & $[0.797,0.817]$ \\'}
    IC_RUIM = {'x.tex': r'\pfA{0.907} & $[0.797,0.817]$ \\'}
    assert confere(IC_BOM)[0], '⛔ reprovou um ponto dentro do intervalo'
    assert not confere(IC_RUIM)[0], '⛔ NAO separa: ponto fora do proprio intervalo passou'
    print('  autoteste ✅ (uma porcentagem trocada REPROVA)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok, ruins, n_par, n_k, n_ic = confere()
    print('  %d pares «n/N (pct %%)», %d kappas e %d intervalos conferidos contra a '
          'propria tabela' % (n_par, n_k, n_ic))
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
