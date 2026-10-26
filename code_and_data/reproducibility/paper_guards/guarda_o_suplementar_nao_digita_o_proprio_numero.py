#!/usr/bin/env python3
r"""⛔ PONTEIRO INTERNO DO SUPLEMENTAR COM O NUMERO DIGITADO.

POR QUE EXISTE (14/09/2026). Tirei uma tabela do suplementar e dividi outra em duas. A
primeira mudanca deslocou a numeracao em -1, a segunda em +1, e as duas nao se cancelam
porque atuam em faixas diferentes. Resultado: **sete** ponteiros internos passaram a
nomear outro experimento — a legenda da S23 mandava o leitor a «S18» para valores por
operacao, e a S18 e a matriz de cobertura; a S24 mandava a «S17 e S23» para o inventario
e as formulas, que estao na S16 e na S22; dois titulos «(continued)» anunciavam S11 e S12
quando continuavam a S10 e a S11.

🔴 O QUE DEIXOU PASSAR. A `guarda_ponteiros_ao_suplementar.py` confere os ponteiros que
saem do CORPO, onde `\ref` nao atravessa e o numero *tem* de ser digitado. Dentro do
suplementar `\ref` funciona — e ninguem usava. Nenhuma guarda olhava para ca, e o defeito
e invisivel a leitura: o numero EXISTE, so aponta para a tabela errada.

⭐ A REGRA. Um arquivo do suplementar nao digita «Table S<n>»: escreve `\ref{rotulo}`, que
se renumera sozinho. A unica excecao e a frase que ENSINA a convencao ao leitor, e ela
fica declarada aqui pelo texto, nao por numero de linha.
"""
import re, sys
from pathlib import Path

A = Path(__file__).parent

# ⚠️ a frase que explica a convencao precisa mostrar o formato; e o unico lugar onde o
#    «S1» nao e ponteiro para tabela nenhuma.
ISENTOS = ('article cites these tables as Table~S1, Table~S2, and so on.',
           'which cites these tables as\nTable~S1, Table~S2, and so on.',)

DIGITADO = re.compile(r'(?:Tables?|Figs?\.|Figures?)~?\s*S\d+')

# ⭐ O SENTIDO INVERSO, que tambem nao tem `\ref`: o suplementar cita SECAO do corpo pelo
#    numero digitado. Aqui o numero nao se resolve sozinho, entao o que se pode garantir e
#    que ele bate com o `main.aux`. Cada entrada liga um TRECHO da legenda ao rotulo que ela
#    de fato quer. Ponteiro novo sem entrada aqui REPROVA: e assim que se descobre que
#    alguem digitou um numero que ninguem confere.
SECAO = {
    'whose three conditions are stated there': 'sec:screen',
    'under the rule stated in Section': 'sec:methods',
    'under the polarity-permissive rule of': 'sec:methods',
    # ⭐ 23/09 (parecer v8): os dois ponteiros novos do suplementar para o corpo.
    'the primary source-aware block interval for the technical branch is': 'sec:menu',
    'The seventeen operations of the auxiliary comparison in': 'sec:class',
    'the primary interval of Section': 'sec:screen_results',
}
SECAO_RE = re.compile(r'Section~?([\d.]+) of the main text')


def _arquivos():
    """supplementary.tex e todo .tex que ele inclui."""
    sup = A / 'supplementary.tex'
    t = sup.read_text(errors='replace')
    saida = [sup]
    for m in re.finditer(r'\\input\{([^}]+)\}', t):
        q = A / (m.group(1) if m.group(1).endswith('.tex') else m.group(1) + '.tex')
        if q.exists():
            saida.append(q)
    return saida


def digitados(texto):
    """Ocorrencias de numero digitado, fora de comentario e fora da frase isenta."""
    for isento in ISENTOS:
        texto = texto.replace(isento, '')
    achados = []
    for i, l in enumerate(texto.splitlines(), 1):
        if l.lstrip().startswith('%'):
            continue
        l = re.sub(r'(?<!\\)%.*$', '', l)          # comentario no fim da linha
        for m in DIGITADO.finditer(l):
            achados.append((i, m.group(0), l.strip()[:90]))
    return achados


def ref_mutilado(texto):
    r"""⛔ 14/09, meia hora depois: troquei o numero por `\ref` num gerador de string
    NAO-raw. Em Python `\r` e um RETORNO DE CARRO, entao `\ref{tab:literature}` virou
    CR + `ef{...}` e o PDF imprimiu «Table eftab:literature». A guarda de cima aprovou:
    numero digitado ja nao havia. ⚠️ Quem achou foi LER O PDF — e por isso a perna
    entra aqui, onde roda sozinha.
    """
    return [(i, repr(l[:70])) for i, l in enumerate(texto.split('\n'), 1) if '\r' in l]


def ref_sem_rotulo(texto, rotulos):
    r"""Um \ref que nao casa rotulo nenhum imprime «??» e passa despercebido."""
    return [m for m in re.findall(r'\\ref\{([^}]+)\}', texto) if m not in rotulos]


def _rotulos():
    aux = A / 'supplementary.aux'
    if not aux.exists():
        return None                      # sem .aux nao se decide; nao se inventa
    return set(re.findall(r'\\newlabel\{([^}]+)\}', aux.read_text(errors='replace')))


def secao_errada(texto, numero_de):
    """Cada «Section N of the main text» tem de bater com o rotulo declarado em SECAO."""
    ruins = []
    for m in SECAO_RE.finditer(texto):
        ini = max(texto.rfind('. ', 0, m.start()), 0)
        janela = texto[ini:m.end() + 160]
        rot = next((r for trecho, r in SECAO.items() if trecho in janela), None)
        if rot is None:
            ruins.append((m.group(1), 'sem entrada em SECAO: ninguem confere este numero'))
        elif numero_de.get(rot) != m.group(1):
            ruins.append((m.group(1), f'{rot} e {numero_de.get(rot)} no main.aux'))
    return ruins


def _secoes_do_corpo():
    aux = A / 'main.aux'
    if not aux.exists():
        return None
    return {m.group(1): m.group(2) for m in
            re.finditer(r'\\newlabel\{(sec:[^}]+)\}\{\{([\d.]+)\}', aux.read_text(errors='replace'))}


def main():
    ruins = []
    for q in _arquivos():
        for i, s, ctx in digitados(q.read_text(errors='replace')):
            ruins.append((q.name, i, s, ctx))
    rot, secs = _rotulos(), _secoes_do_corpo()
    for q in _arquivos():
        texto = q.read_text(errors='replace')
        if secs is not None:
            for n, por in secao_errada(texto, secs):
                ruins.append((q.name, 0, f'Section {n} do corpo', por))
        for i, ctx in ref_mutilado(texto):
            ruins.append((q.name, i, 'CR no lugar de \\ref', ctx))
        if rot is not None:
            for r in ref_sem_rotulo(texto, rot):
                ruins.append((q.name, 0, f'\\ref{{{r}}} sem rotulo', 'imprimiria ??'))
    if ruins:
        print(f'  ⛔ {len(ruins)} ponteiro(s) do suplementar digitam o numero em vez de \\ref:')
        for n, i, s, ctx in ruins:
            print(f'       {n}:{i}  «{s}»  em: {ctx}')
        print('     troque por \\ref{rotulo}: o numero passa a vir do .aux e nao envelhece.')
        return 1
    print('  ✅ nenhum ponteiro interno do suplementar digita o proprio numero')
    return 0


def autoteste():
    """Duas pernas: aprova o estado certo e REPROVA o defeito que existiu de verdade."""
    certo = r'Per-operation values are in Table~\ref{tab:literature} and per-model ' \
            r'values in Table~\ref{tab:screening}.'
    errado = 'Per-operation values are in Table~S18 and per-model values in Table~S21.'
    isento = 'article cites these tables as Table~S1, Table~S2, and so on.'
    comentario = '%% --- S11: tab:e2e --- este comentario nao e ponteiro'
    casos = [(certo, 0, 'a legenda com \\ref'),
             (errado, 2, 'o defeito real de 14/09: S18 e S21 digitados'),
             (isento, 0, 'a frase que ensina a convencao ao leitor'),
             (comentario, 0, 'numero dentro de comentario')]
    mal = 0
    for txt, esperado, nome in casos:
        n = len(digitados(txt))
        ok = n == esperado
        mal += not ok
        print(f"  {'✅' if ok else '⛔'} {nome}: achou {n}, esperado {esperado}")
    # a guarda tem de estar LENDO os arquivos, nao uma lista vazia
    mutilado = 'by any source, whereas Table~\ref{tab:literature} orients each'
    n = len(ref_mutilado(mutilado))
    print(f"  {'✅' if n == 1 else '⛔'} o \\ref virado CR de 14/09: achou {n}, esperado 1")
    mal += n != 1
    n = len(ref_mutilado(r'whereas Table~\ref{tab:literature} orients each'))
    print(f"  {'✅' if n == 0 else '⛔'} o mesmo trecho com \\ref inteiro: achou {n}, esperado 0")
    mal += n != 0
    n = len(ref_sem_rotulo(r'ver \ref{tab:naoexiste} e \ref{tab:literature}', {'tab:literature'}))
    print(f"  {'✅' if n == 1 else '⛔'} \\ref sem rotulo: achou {n}, esperado 1")
    mal += n != 1
    secs = {'sec:screen': '3.5', 'sec:methods': '3.3'}
    ok = 'The three families under the screening rule of Section~3.5 of the main text, ' \
         'whose three conditions are stated there.'
    mau = ok.replace('3.5', '3.4')
    orfao = 'as described in Section~9.9 of the main text, with no entry declared.'
    for txt, esperado, nome in ((ok, 0, 'Secao 3.5 casando o rotulo sec:screen'),
                                (mau, 1, 'a mesma frase com 3.4: numero que existe, secao errada'),
                                (orfao, 1, 'ponteiro de secao que ninguem declarou')):
        n = len(secao_errada(txt, secs))
        print(f"  {'✅' if n == esperado else '⛔'} {nome}: achou {n}, esperado {esperado}")
        mal += n != esperado
    arqs = _arquivos()
    if len(arqs) < 10:
        print(f'  ⛔ so {len(arqs)} arquivo(s) coletados: bug do leitor, nao resultado')
        mal += 1
    else:
        print(f'  ✅ coleta {len(arqs)} arquivos do suplementar')
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
