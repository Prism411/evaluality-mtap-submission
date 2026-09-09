#!/usr/bin/env python3
"""⛔ A CONVENCAO DE TERMOS SEGURA DO COMECO AO FIM?

POR QUE EXISTE (08/09/2026). O artigo audita a LEITURA que a literatura faz de um estagio do
pipeline. Se o texto ora chama o estagio de «visual-selection» ora de «visual-quality», o
revisor confunde o que o HSMVideoSumm queria fazer com o que este artigo audita — e essa
confusao e exatamente a que o artigo existe para desfazer.

A convencao, rigida:
  `visual-selection stage`     a arquitetura;
  `visual-selection operation` o componente posto no estagio;
  `technical-quality ...`      o CONSTRUTO auditado (interpretacao, escore, proxy);
  `deployed ... operation`     o caso implantado.

⛔ Entao «visual-quality» e «visual quality» nao aparecem no corpo. ⚠️ COM UMA EXCECAO
DECLARADA: trecho literal de fonte. Mudar a frase de outro autor e citar errado, e varias
fontes dizem «visual quality» — e justamente por dizerem isso que elas entram no artigo.

Autoteste de duas pernas: o corpo atual passa, e reintroduzir o termo REPROVA.
"""
import io
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
# ⛔ o resumo grafico ficou de fora na primeira versao e era JUSTAMENTE onde o termo
# sobrevivia, na primeira linha que o leitor ve. Guarda que nao le o arquivo aprova por
# nao olhar.
CORPO = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex', 'sec_results.tex',
         'sec_discussion.tex', 'sec_conclusion.tex', 'main.tex',
         'graphical_abstract.tex', 'supplementary.tex']
PROIBIDO = re.compile(r'visual[- ]quality', re.I)
# trecho literal de fonte: `\emph{``...''}` ou `\textit{``...''}`
CITACAO = re.compile(r'\\(?:emph|textit)\{\s*``.*?\'\'\s*\}', re.S)


def limpa(t):
    """Tira os trechos literais de fonte, que ficam fora da convencao por direito."""
    return CITACAO.sub(' CITACAO ', t)


def confere(textos=None):
    ruins = []
    fontes = textos if textos is not None else {
        f: (AQUI / f).read_text(encoding='utf-8') for f in CORPO if (AQUI / f).exists()}
    n = 0
    for f, t in fontes.items():
        t = limpa(t)
        for i, linha in enumerate(t.split('\n'), 1):
            if linha.lstrip().startswith('%'):
                continue
            n += 1
            for m in PROIBIDO.finditer(linha):
                ini = max(0, m.start() - 50)
                ruins.append('%s:%d  ...%s...' % (f, i, linha[ini:m.end() + 50].strip()))
    return not ruins, ruins, len(fontes)


def autoteste():
    ok, ruins, _ = confere()
    if not ok:
        print('    ⛔ autoteste: o corpo ja usa o termo fora da convencao: %s' % ruins[:2])
        return False
    # ⛔ a perna que separa: reintroduzir o termo tem de reprovar
    doente = {'x.tex': 'The visual-quality module receives one frame per second.'}
    if confere(doente)[0]:
        print('    ⛔ autoteste: aprovou «visual-quality» reintroduzido')
        return False
    # ⚠️ e a excecao declarada tem de continuar valendo: citacao literal passa
    cit = {'x.tex': "the source states \\emph{``the visual quality is the combination of "
                    "contrast, blur, and image skew measures''} for its objective."}
    if not confere(cit)[0]:
        print('    ⛔ autoteste: reprovou um trecho literal de fonte, que e excecao declarada')
        return False
    print('   autoteste ✅ (reprova o termo reintroduzido; aceita trecho literal de fonte)')
    return True


if __name__ == '__main__':
    if not autoteste():
        sys.exit(1)
    ok, ruins, n = confere()
    print('  %d arquivos do corpo conferidos contra a convencao de termos' % n)
    for x in ruins[:8]:
        print('    ⛔ %s' % x)
    print('  %s' % ('✅ APROVA' if ok else '⛔ REPROVA'))
    sys.exit(0 if ok else 1)
