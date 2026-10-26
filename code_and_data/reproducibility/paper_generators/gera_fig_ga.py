#!/usr/bin/env python3
"""Textura de ruido e keypoints do resumo grafico, em TikZ.

⛔ POR QUE ISTO E UM GERADOR. O desenho de origem produz o ruido com
`Math.random()` no navegador: cada abertura da pagina da uma textura diferente.
Uma peca de submissao nao pode mudar a cada build, e este repositorio tem uma
guarda so para isso (`guarda_o_gerador_e_deterministico.py`). Aqui a semente e
fixa e o `.tex` emitido e byte-identico a cada rodada.

⭐ Os keypoints usam o MESMO gerador congruencial do desenho de origem
(s=7, s = s*16807 mod 2147483647), entao as 34 posicoes saem nas mesmas
coordenadas que o autor do desenho viu.

⚠️ Nada aqui e medicao: sao coordenadas de ilustracao. Nenhum numero do artigo
passa por este arquivo; os numeros do resumo grafico vem de `regras_publicadas`.
"""
import random
from pathlib import Path

AQUI = Path(__file__).parent
ALTURA = 725  # o eixo y do TikZ cresce para cima e o do desenho para baixo


def cinza(v):
    """0..255 -> `black!N`, a escala que o TikZ entende."""
    return max(0, min(100, round(100 - v / 255 * 100)))


def bloco(x, y, w, h, nx, ny, semente, opacidade):
    """Um retalho de ruido de `nx` por `ny` celulas cobrindo (x,y,w,h)."""
    r = random.Random(semente)
    cw, ch = w / nx, h / ny
    saida = []
    for j in range(ny):
        for i in range(nx):
            v = 128 + (r.random() - 0.5) * 170
            saida.append(
                '\\fill[black!%d,opacity=%.2f] (%.2f,%.2f) rectangle ++(%.3f,-%.3f);'
                % (cinza(v), opacidade, x + i * cw, ALTURA - (y + j * ch), cw, ch))
    return saida


def keypoints():
    """As 34 posicoes do desenho de origem, pelo mesmo LCG."""
    s = 7
    def r():
        nonlocal s
        s = (s * 16807) % 2147483647
        return s / 2147483647
    pts = []
    while len(pts) < 34:
        x, y = r() * 138, r() * 138
        if (x - 69) ** 2 + (y - 69) ** 2 < 57 ** 2:
            pts.append((x, y))
    return pts


def main():
    linhas = ['%% GERADO por gera_fig_ga.py -- nao editar a mao.',
              '%% Ruido deterministico e keypoints do resumo grafico.']

    # o quadro «noisy» do painel 2, e o do painel 3, na mesma granulacao do
    # desenho de origem (grain 64 -> 64x36); o da lupa e quadrado (22x22).
    linhas.append('\\newcommand{\\gaRuidoTeste}{%')
    linhas += bloco(694, 190, 212, 120, 56, 32, 11, 0.40)
    linhas.append('}')
    linhas.append('\\newcommand{\\gaRuidoPorque}{%')
    linhas += bloco(957, 190, 212, 120, 56, 32, 23, 0.40)
    linhas.append('}')
    linhas.append('\\newcommand{\\gaRuidoLupa}{%')
    linhas += bloco(1113, 245, 150, 150, 22, 22, 5, 0.50)
    linhas.append('}')

    linhas.append('\\newcommand{\\gaKeypoints}{%')
    for x, y in keypoints():
        linhas.append('\\fill[kpazul,draw=white,line width=0.25mm] (%.2f,%.2f) circle (6.5);'
                      % (1113 + x, ALTURA - (245 + y)))
    linhas.append('}')

    alvo = AQUI / 'fig_ga_ruido.tex'
    alvo.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    print('  %s  (%d linhas, semente fixa)' % (alvo.name, len(linhas)))


if __name__ == '__main__':
    main()
