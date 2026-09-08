#!/usr/bin/env python3
"""⛔ TODO «Table~SN» / «Fig.~SN» DO CORPO EXISTE NO SUPLEMENTAR?

POR QUE EXISTE (07/09/2026). O corpo prometia «Table~S1 of the supplement carries the
correspondence» e a tabela de rastreio era a **S17**. Como sao dois documentos separados,
o `\\ref` do LaTeX nao alcanca: o numero e DIGITADO, e nada reprova quando ele envelhece.
Bastou a tabela mudar de posicao no suplementar para o corpo apontar para outra coisa.

O QUE ELA FAZ: le os rotulos que o `supplementary.aux` de fato produziu e exige que todo
numero citado no corpo exista la.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']


def existentes(aux=None, especie=None):
    """Os S-numeros que o suplementar produziu, opcionalmente de uma especie so.

    ⚠️ Tabela e figura tem CONTADORES SEPARADOS, entao «Table S4» e «Figure S4» sao objetos
    diferentes e ambos existem: em 08/09 o suplementar tinha tabelas S1--S26 e figuras
    S1--S4. Conferir so o numero deixaria «Table~S3» passar apontando para uma FIGURA.
    """
    txt = (aux or (AQUI / 'supplementary.aux')).read_text()
    pref = {'tab': 'tab', 'fig': 'fig'}.get(especie, '(?:tab|fig)')
    return {m.group(1) for m in
            re.finditer(r'\\newlabel\{' + pref + r':[^}]*\}\{\{(S\d+)\}', txt)}


def citados(arquivos=None):
    """Os S-numeros que o corpo cita, com arquivo, linha e ESPECIE citada."""
    out = []
    for nome in (arquivos or CORPO):
        p = Path(nome) if Path(nome).is_absolute() else AQUI / nome
        if not p.exists():
            continue
        for i, linha in enumerate(p.read_text().split('\n'), 1):
            for m in re.finditer(r'(Tables?|Figs?\.|Figures?)~?~?(S\d+)', linha):
                esp = 'tab' if m.group(1).startswith('Table') else 'fig'
                out.append((nome, i, m.group(2), esp))
    return out


def especie_confere():
    """Todo «Table~Sx» e mesmo tabela, e todo «Figure~Sx» e mesmo figura?"""
    tabs, figs = existentes(especie='tab'), existentes(especie='fig')
    erradas = []
    for nome, i, s, esp in citados():
        alvo = tabs if esp == 'tab' else figs
        if s not in alvo:
            erradas.append('%s:%d cita %s como %s, e nao existe assim' % (nome, i, s, esp))
    return not erradas, erradas


# ⛔ IDENTIDADE, nao so existencia. Em 07/09 inserir uma tabela no suplementar empurrou o
# rastreio de S17 para S18, e o corpo continuou dizendo S17 — que EXISTE, e passava.
# Cada entrada liga um trecho do corpo ao rotulo que ele deve estar citando.
ESPERADO = {
    'carries the correspondence': 'tab:trace',
    'visible in the equation before any measurement': 'tab:ct',
    'shows both distributions': 'fig:menu',
}


def numeros_reais(aux=None):
    """rotulo -> S-numero que o suplementar de fato atribuiu."""
    txt = (aux or (AQUI / 'supplementary.aux')).read_text()
    return {m.group(1): m.group(2) for m in
            re.finditer(r'\\newlabel\{([^}]*)\}\{\{(S\d+)\}', txt)}


def identidade(arquivos=None):
    """Cada ponteiro do corpo cita o S-numero do rotulo CERTO?"""
    reais, ruins = numeros_reais(), []
    for nome in (arquivos or CORPO):
        q = Path(nome) if Path(nome).is_absolute() else AQUI / nome
        if not q.exists():
            continue
        for i, linha in enumerate(q.read_text().split('\n'), 1):
            for trecho, rot in ESPERADO.items():
                if trecho not in linha:
                    continue
                cit = re.findall(r'(?:Table|Fig\.|Figure)~?(S\d+)', linha)
                alvo = reais.get(rot)
                if alvo and cit and alvo not in cit:
                    ruins.append((nome, i, rot, alvo, cit))
    return not ruins, ruins


def confere(arquivos=None):
    tem = existentes()
    assert tem, '⛔ nenhum rotulo S no supplementary.aux: rodar pdflatex antes'
    vistos = citados(arquivos)
    assert vistos, '⛔ zero ponteiros lidos: aprovaria no vacuo'
    ruins = [(f, i, n) for f, i, n, _e in vistos if n not in tem]
    return not ruins, ruins, tem


def _autoteste():
    """⭐ So vale se REPROVAR quando o ponteiro quebra. Aqui o defeito volta de verdade."""
    import tempfile
    ok, _, _ = confere()
    assert ok, 'o estado atual deveria passar'
    with tempfile.TemporaryDirectory() as td:
        bom = Path(td) / 'bom.tex'
        bom.write_text('vide Table~S17 do suplementar\n')
        ruim = Path(td) / 'ruim.tex'
        ruim.write_text('vide Table~S99 do suplementar\n')
        # ⭐ as DUAS pernas: passa no mundo certo E reprova no mundo errado
        assert confere([str(bom)])[0], '⛔ reprova um ponteiro valido'
        mau, quais, _ = confere([str(ruim)])
        assert not mau and quais[0][2] == 'S99', '⛔ NAO pega o ponteiro quebrado'
    return True


def _autoteste_especie():
    """⭐ Tabela e figura tem contadores separados: «Table~S3» apontando para uma FIGURA
    tem de reprovar, e conferir so o numero nao separaria isso."""
    tabs, figs = existentes(especie='tab'), existentes(especie='fig')
    assert tabs and figs, '⛔ nao li as duas especies do .aux'
    so_fig = figs - tabs
    if not so_fig:
        return True   # nao ha numero exclusivo de figura para montar o mundo errado
    n = sorted(so_fig)[0]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td) / 'x.tex'
        q.write_text('vide Table~%s do suplementar\n' % n)
        maus = [c for c in citados([str(q)]) if c[2] not in tabs]
        assert maus, '⛔ NAO separa: «Table~%s» apontando para figura passou' % n
    return True


if __name__ == '__main__':
    assert _autoteste()
    assert _autoteste_especie()
    ok, ruins, tem = confere()
    ok2, trocados = identidade()
    ok3, erradas = especie_confere()
    print(f'  autoteste ✅   {len(tem)} rotulos S no suplementar')
    print(f'  {"✅" if ok2 else "⛔"} identidade: cada ponteiro cita o rotulo certo')
    print(f'  {"✅" if ok3 else "⛔"} especie: «Table~Sx» e tabela, «Figure~Sx» e figura')
    for x in erradas:
        print(f'    {x}')
    for f, i, rot, alvo, cit in trocados:
        print(f'    {f}:{i} devia citar {alvo} ({rot}) e cita {cit}')
    ok = ok and ok2 and ok3
    print(f'  {len(citados())} ponteiros no corpo')
    print(f'  {"✅ APROVA" if ok else "⛔ REPROVA"}')
    for f, i, n in ruins:
        print(f'    {f}:{i} aponta para {n}, que nao existe')
    sys.exit(0 if ok else 1)
