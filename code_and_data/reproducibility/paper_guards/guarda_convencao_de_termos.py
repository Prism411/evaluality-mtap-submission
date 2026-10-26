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
  `HSMVideoSumm ... operation` a operacao auditada que vem do sistema.
⛔ 25/09: `deployed` SAIU (decisao do [author]). Era residuo do enquadramento antigo, em
que o artigo tratava o SIFT+BoVW como «o nosso caso implantado». Ele e um dos
TRABALHOS AUDITADOS: o metodo e da tese da Barbieri e a implementacao e a do Leonardo.

⭐ 14/09, AMPLIADA. Um parecer notou que «quality criterion» nao aparecia no artigo, e que
`criterion` significava quatro coisas diferentes sem aviso. A distincao e VERIFICAVEL no
codigo do sistema implantado: `core/selection_criteria/` tem cinco criterios (chronology,
introduction, quality, redundancy, subjectivity) e `QualityPick` recebe uma
`ScoringStrategy` PLUGAVEL, com `SIFTBoVWStrategy()` por padrao. **Trocar o metodo nao troca
o criterio.** 📄 `o_criterio_e_fixo_e_o_metodo_e_plugavel.json`
  `quality criterion`             o objeto do artigo, fixo em todas as comparacoes;
  `implementation`                amostragem + metodo de pontuacao + agregacao;
  `scoring method`                a computacao que produz o numero;
  `method-eligibility conditions` o que aprova METODO, nao conteudo de resumo;
  `inventory inclusion rule`      o que admite uma operacao na pesquisa;
  `provenance classification rule` o que classifica o papel na fonte.
⛔ E `slot` sai: era o termo que fazia o criterio parecer um lugar vazio.
⚠️ MAS o criterio que a TESE deriva para esse estagio e de RELEVANCIA, nao de qualidade —
nomear o estagio do sistema implantado nao autoriza reescrever a fonte historica.

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

# ⛔ termos que a convencao de 14/09 aposentou no corpo, com o substituto declarado
APOSENTADOS = {
    r'\bslot\b': 'quality criterion / implementation',
    r'visual-content stage': 'quality criterion',
    # ⛔ 27/09: `deployed` estava APOSENTADO NO DOCSTRING desde 25/09 e nunca
    # entrou nesta lista -- a guarda enunciava a regra e nao a cobrava. Foi por
    # isso que `Deployed SIFT+BoVW` sobreviveu no resumo grafico, na primeira
    # linha que o leitor ve, depois de o corpo inteiro ter sido limpo.
    r'\bdeployed\b': 'HSMVideoSumm / audited operation',
}
# ⛔ o resumo grafico ficou de fora na primeira versao e era JUSTAMENTE onde o termo
# sobrevivia, na primeira linha que o leitor ve. Guarda que nao le o arquivo aprova por
# nao olhar.
# ⛔ e a segunda ampliacao, no mesmo dia: os `\input` de tabela tambem ficavam de fora,
# e la o termo aparecia em legenda. A guarda le TODOS os .tex da pasta; linha de comentario
# e trecho literal de fonte continuam fora, por direito.
CORPO = sorted(p.name for p in Path(__file__).parent.glob('*.tex'))
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
            for pat, subst in APOSENTADOS.items():
                # ⛔ 27/09: sem `re.I` a lista so pegava a forma minuscula. O
                # `PROIBIDO` ja era insensivel a caixa e este laco nao era, entao
                # «Deployed» no inicio de uma linha da figura passava enquanto
                # «deployed» no meio de uma frase reprovava.
                for m in re.finditer(pat, linha, re.I):
                    ini = max(0, m.start() - 44)
                    ruins.append('%s:%d  «%s» aposentado, use «%s»: ...%s...'
                                 % (f, i, m.group(0), subst, linha[ini:m.end() + 40].strip()))
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
    # ⛔ e a perna de 14/09: «slot» de volta tem de reprovar
    if confere({'x.tex': 'the operation placed in that slot is evaluated here.'})[0]:
        print('    ⛔ autoteste: aprovou «slot», que a convencao de 14/09 aposentou')
        return False
    # ⛔ e a perna de 27/09: `deployed` de volta tem de reprovar. A redacao
    # abaixo e a HISTORICA, a que sobreviveu no resumo grafico -- um controle
    # escrito a partir do texto atual passaria no caso que ja aconteceu.
    if confere({'x.tex': 'Deployed SIFT$+$BoVW \\textbf{65.1\\%}'})[0]:
        print('    ⛔ autoteste: aprovou «deployed», aposentado em 25/09')
        return False
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
