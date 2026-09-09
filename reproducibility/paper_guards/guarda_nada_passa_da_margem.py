#!/usr/bin/env python3
"""⛔ ALGUMA COISA IMPRESSA PASSA DA MARGEM?

POR QUE EXISTE (08/09/2026). O log do LaTeX trazia quatro `Overfull \\hbox` no suplementar, e
`Overfull` nao e erro: a suite dizia ✅ e o PDF tinha tabela entrando **11 mm** na margem.
Ninguem le o log inteiro a cada rodada, e o numero em pt nao diz em que pagina esta.

⭐ COMO SEPARA: renderiza cada pagina e acha a coluna mais a direita com tinta, ignorando
cabecalho e rodape. Compara com a MEDIANA das paginas de mesma paridade, porque a classe
usa margens espelhadas e misturar par com impar cria uma falsa acusacao de 5 px em metade
do documento — foi o que aconteceu na primeira versao desta checagem.

⚠️ Tolerancia de 3 mm: italico e hifen projetam um pouco alem da caixa por desenho da fonte,
e acusar isso seria acusar em massa.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).parent
PDFS = ['main.pdf', 'supplementary.pdf']
DPI = 80
TOL_MM = 3.0


def bordas(pdf, dpi=DPI):
    """[(pagina, coluna mais a direita com tinta)] fora do cabecalho e do rodape."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', str(AQUI / pdf), td + '/p'],
                       check=True, capture_output=True)
        out = []
        for p in sorted(Path(td).glob('p-*.png')):
            im = Image.open(p).convert('L')
            w, h = im.size
            px = im.load()
            y0, y1 = int(.10 * h), int(.92 * h)
            d = 0
            for x in range(w - 1, -1, -1):
                if any(px[x, y] < 200 for y in range(y0, y1, 2)):
                    d = x
                    break
            out.append((int(p.stem.split('-')[-1]), d))
    return out


def confere(medidas=None):
    ruins, n = [], 0
    fontes = medidas if medidas is not None else {
        p: bordas(p) for p in PDFS if (AQUI / p).exists()}
    tol_px = TOL_MM / 25.4 * DPI
    for pdf, b in fontes.items():
        n += len(b)
        for paridade in (0, 1):
            g = [(pg, x) for pg, x in b if pg % 2 == paridade]
            if len(g) < 3:
                continue
            med = sorted(x for _, x in g)[len(g) // 2]
            for pg, x in g:
                if x > med + tol_px:
                    ruins.append('%s p%d: %.1f mm alem da margem das paginas de mesma '
                                 'paridade' % (pdf, pg, (x - med) / DPI * 25.4))
    return not ruins, ruins, n


def autoteste():
    """⚠️ As duas pernas, e a de paridade, que e onde a primeira versao errou."""
    ok, ruins, _ = confere()
    if not ok:
        print('    ⛔ autoteste: ja ha pagina alem da margem: %s' % ruins[:2])
        return False
    med_par, med_imp = 549, 522
    limpo = {'x.pdf': [(i, med_par if i % 2 == 0 else med_imp) for i in range(1, 11)]}
    if not confere(limpo)[0]:
        print('    ⛔ autoteste: acusou um documento sem transbordo')
        return False
    # ⛔ o defeito real: uma pagina 11 mm alem
    doente = {'x.pdf': [(i, med_par if i % 2 == 0 else med_imp) for i in range(1, 11)]}
    doente['x.pdf'][3] = (4, med_par + int(11 / 25.4 * DPI))
    if confere(doente)[0]:
        print('    ⛔ autoteste: aprovou uma pagina 11 mm alem da margem')
        return False
    # ⚠️ e a perna da PARIDADE: margens espelhadas nao podem virar acusacao
    espelhado = {'x.pdf': [(i, med_par if i % 2 == 0 else med_imp) for i in range(1, 11)]}
    if not confere(espelhado)[0]:
        print('    ⛔ autoteste: acusou a margem espelhada, que e do desenho da classe')
        return False
    print('   autoteste ✅ (reprova 11 mm alem; nao acusa a margem espelhada)')
    return True


if __name__ == '__main__':
    try:
        import PIL  # noqa: F401
    except ImportError:
        print('  ⏳ sem PIL: a conferencia de margem nao rodou')
        sys.exit(3)
    if not autoteste():
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d paginas medidas contra a margem, tolerancia %.0f mm' % (n, TOL_MM))
    for x in ruins:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
