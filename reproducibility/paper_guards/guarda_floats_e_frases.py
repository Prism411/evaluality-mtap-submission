#!/usr/bin/env python3
"""⛔ FLOAT QUE NINGUEM CITA, E FAIXA PROMETIDA QUE ENVELHECEU.

POR QUE EXISTE (07/09/2026). Dois defeitos apareceram hoje e nenhum quebrava a compilacao:
  - a `fig_menu` estava incluida e NUNCA citada — figura orfa, que o leitor encontra sem saber
    por que ela esta ali;
  - o resumo tinha «none satisfies both» emendando direto em «Held in the same pipeline»:
    uma frase cortada no meio, sem complemento e sem ponto. So apareceu RENDERIZANDO.

Nenhum teste da suite via os dois, porque LaTeX compila feliz com os dois.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
FONTES = sorted(set(AQUI.glob('*.tex')))


def _corpo(p):
    """Texto do .tex sem comentario de linha."""
    return '\n'.join(re.sub(r'(?<!\\)%.*$', '', l) for l in p.read_text().split('\n'))


def numeros_do_suplementar():
    """rotulo -> S-numero, do aux que o suplementar de fato produziu."""
    aux = AQUI / 'supplementary.aux'
    if not aux.exists():
        return {}
    return {m.group(1): m.group(2) for m in
            re.finditer(r'\\newlabel\{([^}]*)\}\{\{(S\d+)\}', aux.read_text())}


def floats_orfaos():
    """Rotulo definido que ninguem alcanca.

    ⚠️ `\\ref` NAO atravessa os dois documentos: o corpo cita tabela do suplementar pelo
    NUMERO literal («Table~S17»). Contar so `\\ref` acusava 20 orfaos, dos quais 18 eram
    citados assim. Um float so e orfao se nem o `\\ref` nem o numero S o alcancam.
    """
    todo = '\n'.join(_corpo(p) for p in FONTES)
    definidos = set(re.findall(r'\\label\{((?:fig|tab):[^}]+)\}', todo))
    citados = set(re.findall(r'\\ref\{((?:fig|tab):[^}]+)\}', todo))
    sn = numeros_do_suplementar()
    # ⚠️ So conta citacao vinda do CORPO e em contexto de citacao. Um `S\\d+` solto
    # casava o cabecalho da propria tabela no suplementar e escondia a `tab:cat` (S5).
    corpo = '\n'.join(_corpo(q) for q in FONTES if q.name != 'supplementary.tex')
    por_numero = set()
    for m in re.finditer(r'(?:Table|Tables|Fig\.|Figure|Figures)~?\s*S(\d+)'
                         r'(?:\s*(-{2,}|and)\s*S(\d+))?', corpo):
        a, lig, b = m.group(1), m.group(2), m.group(3)
        # ⚠️ «and» lista DOIS numeros; so «--» e intervalo. Tratar «and» como
        # intervalo fazia «S1 and S16» cobrir 1..16 e esconder toda orfa no meio.
        por_numero.add(a)
        if b:
            por_numero |= ({str(k) for k in range(int(a), int(b) + 1)}
                           if lig and lig != 'and' else {b})
    por_numero = {f'S{n}' for n in por_numero}
    alcancados = citados | {r for r, n in sn.items() if n in por_numero}
    return sorted(definidos - alcancados)


# ⛔ AQUI HAVIA UM DETECTOR DE «FRASE CORTADA NO MEIO», E ELE FOI REMOVIDO.
#
# A ideia era achar a assinatura do corte: minuscula seguida de Maiuscula sem pontuacao.
# Medido, ele nao separa nada:
#   - 32 candidatos no artigo, TODOS falsos (Title Case do titulo, «naive Bayes»,
#     «Spearman», «Steiger», «Mean Opinion Scores», «while Table», «under Code»);
#   - e no defeito REAL que o motivou, «none satisfies both Held in the same pipeline»,
#     ele passa batido, porque «both» estava na lista de palavras que legitimamente
#     antecedem maiuscula — a mesma lista que reduzia os falsos positivos.
#
# 📌 Instrumento que erra em 32 de 32 e falha no unico caso verdadeiro nao vai para a suite.
# O que achou aquele defeito foi RENDERIZAR e LER a pagina, e nao ha atalho para isso.

def faixa_prometida(corpo=None):
    """As faixas «Tables S1--SN» e «Figures S1--SM» do corpo cobrem o que o suplementar
    de fato produziu?

    ⚠️ Existe uma referencia GUARDA-CHUVA na declaracao de disponibilidade. Ela envelhece em
    silencio: eu acrescentei a S17 e o corpo continuou prometendo «S1--S16».

    ⛔ E em 08/09 ela envelheceu DE OUTRO JEITO que esta guarda nao via: a `fig_inversao`
    foi para o suplementar, que passou a ter QUATRO figuras, e o corpo continuou prometendo
    «Supplementary Figure S1», no singular. A guarda so olhava rotulos `tab:` e aprovava.
    Agora ela confere as duas familias, cada uma contra os seus rotulos.
    """
    if corpo is None:
        corpo = '\n'.join(_corpo(q) for q in FONTES if q.name != 'supplementary.tex')
    aux = (AQUI / 'supplementary.aux').read_text()
    msgs, ok = [], True
    achou = False
    for fam, pref in (('Tables', 'tab'), ('Figures', 'fig')):
        m = re.search(fam + r'\s+S(\d+)\s*-{2,}\s*S(\d+)', corpo)
        reais = [int(x) for x in
                 re.findall(r'\\newlabel\{' + pref + r':[^}]*\}\{\{S(\d+)\}', aux)]
        maior = max(reais) if reais else 0
        if m is None:
            # sem faixa: so passa se o suplementar tiver no maximo um item dessa familia
            if maior > 1:
                ok = False
                msgs.append('%s: o corpo nao promete faixa e o suplementar tem %d'
                            % (fam, maior))
            continue
        achou = True
        prometido = int(m.group(2))
        if prometido < maior:
            ok = False
        msgs.append('%s promete ate S%d, o suplementar vai ate S%d'
                    % (fam, prometido, maior))
    if not achou and not msgs:
        return True, 'nenhuma faixa guarda-chuva no corpo'
    return ok, '; '.join(msgs)


def logs_limpos(logs=None):
    """Os dois .log fecharam sem erro E sem remissao indefinida?

    ⚠️ Mover float entre os documentos leva o uso mas nao a DEFINICAO. Em 07/09 a figura do
    mecanismo foi para o suplementar usando `accentpurple`, que so o corpo definia, e o
    suplementar compilou com 4 erros de xcolor. O PDF ate saiu; so o .log denunciava.

    ⛔ E em 08/09 escapou de OUTRO jeito: `\ref` nao atravessa documentos, entao a
    `tab_familias`, ao mudar para o suplementar, ficou com `\ref{sec:screen}` apontando
    para um rotulo do CORPO. Isso nao gera erro `!`, gera «Reference undefined», e esta
    funcao so contava erros. Agora conta os dois.
    """
    out = {}
    fontes = logs if logs is not None else {
        n: (AQUI / n).read_text(errors='ignore') if (AQUI / n).exists() else None
        for n in ('main.log', 'supplementary.log')}
    for nome, txt in fontes.items():
        if txt is None:
            out[nome] = None
            continue
        erros = sum(1 for l in txt.split('\n') if l.startswith('! '))
        indef = len(re.findall(r'(?:Reference|Citation) `[^\']*\' on page \d+ undefined', txt))
        out[nome] = erros + indef
    return all(v == 0 for v in out.values() if v is not None), out


def _autoteste():
    """⭐ Duas pernas: o estado atual passa, e o defeito reintroduzido REPROVA."""
    # ⚠️ o autoteste prova o DETECTOR, nao o estado do artigo: um artigo sujo nao pode
    # impedir a guarda de rodar. O veredito do estado sai no `main`, com codigo de saida.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td) / 'x.tex'
        q.write_text('\\label{fig:zz} e nada cita\n')
        defs = set(re.findall(r'\\label\{((?:fig|tab):[^}]+)\}', q.read_text()))
        assert 'fig:zz' in defs and not set(re.findall(r'\\ref\{[^}]*\}', q.read_text())), \
            '⛔ a deteccao de orfao nao discrimina'

    # ⭐ a faixa guarda-chuva, nas tres versoes. A do meio e o defeito real de 08/09:
    # a `fig_inversao` foi para o suplementar e o corpo continuou no singular.
    CERTO = 'Supplementary Tables S1--S26, Supplementary Figures S1--S4 and an archive.'
    SO_UMA_FIGURA = 'Supplementary Tables S1--S26, Supplementary Figure~S1 and an archive.'
    TABELAS_VELHAS = 'Supplementary Tables S1--S16, Supplementary Figures S1--S4 and it.'
    assert faixa_prometida(corpo=CERTO)[0], '⛔ reprovou o mundo certo'
    assert not faixa_prometida(corpo=SO_UMA_FIGURA)[0], \
        '⛔ NAO separa: «Figure S1» no singular passou com quatro figuras no suplementar'
    assert not faixa_prometida(corpo=TABELAS_VELHAS)[0], \
        '⛔ NAO separa: faixa de tabelas desatualizada passou'

    # ⭐ a remissao indefinida, que nao gera erro `!` e por isso escapou em 08/09
    LIMPO = {'x.log': 'Output written on x.pdf (30 pages).'}
    SUJO = {'x.log': "LaTeX Warning: Reference `sec:screen' on page 27 undefined on "
                     'input line 20.'}
    assert logs_limpos(logs=LIMPO)[0], '⛔ reprovou um log limpo'
    assert not logs_limpos(logs=SUJO)[0], \
        '⛔ NAO separa: «Reference undefined» passou por nao ser erro `!`'
    return True


if __name__ == '__main__':
    assert _autoteste()
    ok_log, cont = logs_limpos()
    print(f'  {"✅" if ok_log else "⛔"} compilacao sem erro: {cont}')
    ok_faixa, msg = faixa_prometida()
    print(f'  {"✅" if ok_faixa else "⛔"} faixa prometida: {msg}')
    orf = floats_orfaos()
    print(f'  autoteste ✅   {len(FONTES)} arquivos .tex')
    print(f'  {"✅" if not orf else "⛔"} floats orfaos: {len(orf)} {orf if orf else ""}')
    sys.exit(0 if not orf and ok_faixa and ok_log else 1)
