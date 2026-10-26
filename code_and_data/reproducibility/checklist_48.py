#!/usr/bin/env python3
"""⛔ OS 48 CRITERIOS DA RUBRICA, CONFERIDOS CONTRA O TEXTO ATUAL.

POR QUE EXISTE (21/09/2026). O [author] pediu que os 48 itens estejam cumpridos «em cada
secao e paragrafo». Uma lista lida a olho envelhece na primeira reescrita: esta roda.

⚠️ O QUE ELA PODE E O QUE NAO PODE. Um criterio como «leitura fluida» nao se automatiza.
Cada item abaixo tem um TESTE MECANICO quando existe um, e quando nao existe fica
marcado `JULGAMENTO`, com a evidencia apontada para conferencia humana. ⛔ Um item
`JULGAMENTO` NAO conta como verde automatico: ele conta como «conferido a mao, e aqui esta
onde olhar».

⭐ A regra que separa esta lista de um teatro de conformidade: todo teste mecanico e
NEGATIVO — procura a frase proibida ou a ausencia da obrigatoria. Um teste que so
procurasse a frase boa passaria escrevendo a frase boa.
"""
import re
import sys
from pathlib import Path

A = Path(__file__).parent
SEC = ['sec_intro.tex', 'sec_related.tex', 'sec_method.tex', 'sec_results.tex',
       'sec_discussion.tex', 'sec_conclusion.tex']


def corpo():
    """⛔ Varre TAMBEM as tabelas e figuras: varias exigencias da rubrica (criterio 30,
    unidades e NA nas legendas) vivem no `tab_*.tex`, nao no `sec_*.tex`. Varrer so as
    secoes acusava ausencia de frase que estava escrita — falso positivo que faria
    reescrever o que ja esta certo."""
    t = [(A / f).read_text(encoding='utf-8') for f in SEC]
    t += [q.read_text(encoding='utf-8') for q in sorted(A.glob('tab_*.tex'))]
    t += [q.read_text(encoding='utf-8') for q in sorted(A.glob('fig_*.tex'))]
    return '\n'.join(t)


def sem_comentario(t):
    return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('%'))


def plano(t):
    """⚠️ O LaTeX quebra linha onde quiser. Procurar frase exata num texto com quebras
    devolve ausencia falsa — o mesmo erro que ja custou uma conclusao errada sobre o
    Otani. Normaliza o espaco antes de qualquer busca."""
    return re.sub(r'\s+', ' ', t)


def resumo():
    m = re.search(r'\\abstract\{(.*?)\n\}', (A / 'main.tex').read_text(), re.S)
    return sem_comentario(m.group(1)) if m else ''


def titulo():
    m = re.search(r'\\title\[[^\]]*\]\{(.*?)\}', (A / 'main.tex').read_text(), re.S)
    return m.group(1) if m else ''


def n_palavras_resumo():
    t = re.sub(r'\\[a-zA-Z]+\*?(\{[^}]*\})?', ' ', resumo())
    return len(t.split())


# (n, nome curto, tipo, funcao -> (ok, evidencia))
def checagens():
    c, r, tit = plano(sem_comentario(corpo())), plano(resumo()), plano(titulo())
    todo = c + ' ' + r + ' ' + tit
    P = []

    def proibe(frases, onde=todo):
        achou = [f for f in frases if re.search(f, onde, re.I)]
        return (not achou, 'nenhuma das %d formulacoes proibidas' % len(frases)
                if not achou else 'AINDA PRESENTE: %s' % achou[:2])

    def exige(frases, onde=todo, quantas=1):
        achou = [f for f in frases if re.search(f, onde, re.I)]
        return (len(achou) >= quantas,
                'achou %d de %d exigidas' % (len(achou), len(frases)))

    P.append((1, 'nao restringir a um unico metodo', 'MEC', lambda: exige(
        [r'\\fontesDaLiteratura\{\}', r'no-reference (quality )?models', r'19 convolutional'], quantas=3)))
    P.append((2, 'pipeline como infraestrutura', 'MEC', lambda: proibe(
        [r'any (such )?pipeline would serve', r'nothing (below )?depends on the identity'])))
    P.append((3, 'contribuicao principal explicita', 'MEC', lambda: exige(
        [r'The objective is to establish', r'The study contributes'], quantas=2)))
    P.append((4, 'promessas alinhadas as evidencias', 'MEC', lambda: proibe(
        [r'the three classes the field', r'classes the literature uses are not built',
         r'What the evidence supports is a claim about classes'])))
    P.append((5, 'contribuicao sem modelo novo', 'MEC', lambda: proibe(
        [r'state[- ]of[- ]the[- ]art (summarizer|method) (we|is) propos'])))
    # ⚠️ 22/09: a segunda perna exigia «Read by class, the confirmed corpus» — frase que o
    # parecer v2 mandou REMOVER (V2-011), por apresentar triagem como uso confirmado. Um
    # checklist nao pode exigir o que a rubrica proibe: o padrao passa a ser a redacao que
    # declara o nivel de verificacao ANTES do numero.
    P.append((6, 'revisao fundamenta o desenho', 'MEC', lambda: exige(
        # ⚠️ 27/09: «that is the gap this audit addresses» era metacomentario e saiu na
        # limpeza do tom. A lacuna continua enunciada, sem anunciar-se: «What has not been
        # examined on the selection side is ...». O criterio cobra o FATO, nao a formula.
        [r'What has not been examined on the selection side',
         r'rest on the source-checked inventory'], quantas=2)))
    # ⛔ 22/09 (parecer v2, V2-011/012/045): o criterio 7 exige que a contagem por termos
    # NAO seja apresentada como adocao confirmada. Proibe a formulacao antiga e EXIGE a
    # declaracao do nivel de verificacao, senao basta apagar a frase ruim sem dizer nada.
    P.append((7, 'tabela taxonomica rastreavel', 'MEC', lambda: (
        proibe([r'Classical statistical no-reference IQA', r'confirmed corpus',
                r'\b(?:use|uses) each class'])[0]
        and exige([r'a match implies no reading of the matched work',
                   r'not a systematic mapping'], quantas=2)[0],
        'triagem declarada como triagem'
        if proibe([r'confirmed corpus', r'\b(?:use|uses) each class'])[0]
        else 'AINDA APRESENTA TRIAGEM COMO USO CONFIRMADO')))
    P.append((8, 'classificacoes verificadas na fonte', 'MEC', lambda: exige(
        [r'verbatim excerpt', r'were read in full'], quantas=2)))
    P.append((9, 'nao confundir qualidade com outro objetivo', 'MEC', lambda: exige(
        [r'contains images of\s+interest', r'not a failure of that source',
         r'a separate requirement'], quantas=3)))
    P.append((10, 'representantes justificados', 'MEC', lambda: exige(
        [r'construction of ours used as a diagnostic', r'not applicable'], quantas=2)))
    P.append((11, 'comparacoes adequadas a pergunta', 'MEC', lambda: exige(
        [r'no reference model is involved|uses no reference method'])))
    P.append((12, 'variar so o componente investigado', 'MEC', lambda: exige(
        [r'matched-input control', r'two treatments are reported\s+separately'], quantas=2)))
    P.append((13, 'fidelidade e adaptacoes', 'MEC', lambda: proibe(
        [r'implemented as written', r'published (scoring )?implementations'])))
    P.append((14, 'comparabilidade entre modulos', 'MEC', lambda: exige(
        [r'are not interchangeable'], quantas=1)))
    P.append((15, 'mesmo protocolo', 'MEC', lambda: exige([r'the same bench|the same rule|same protocol'])))
    P.append((16, 'ground truth definido', 'MEC', lambda: exige(
        # ⚠️ 27/09 (cli-3): «not a human judgement» saiu do metodo porque a 5.1 ja diz o mesmo
        # («defined by controlled transformation, not human preference»); regra do parecer:
        # limitacao uma vez, na 5.1.
        [r'fidelity reference the protocol defines', r'not a human judgement|not human preference'], quantas=2)))
    P.append((17, 'falhas como hipoteses', 'MEC', lambda: exige(
        # ⚠️ 27/09: a ressalva saiu da 4 e vive na 5.1, «remains a hypothesis», que e onde
        # este criterio a quer: falha apresentada como hipotese, nao como causa estabelecida.
        # ⚠️ 27/09 (cli-3, parecer do [author]): «remains a hypothesis» saiu por ser ressalva
        # defensiva; o FATO (a explicacao cruzada e alinhamento, nao mecanismo medido) segue
        # em «rests on alignment» na 5 e em «consistent with the noise reversals» na 6.
        [r'rests on alignment', r'does not fail as a block'], quantas=2)))
    P.append((18, 'escore e consequencia', 'MEC', lambda: exige([r'changes \\casCompleta\{\} of the 42'])))
    P.append((19, 'mudanca nao e melhoria', 'MEC', lambda: exige(
        [r'both cross zero|both intervals? .{0,30}cross zero',
         r'preference between whole summaries'], quantas=2)))
    P.append((20, 'generalizacao proporcional', 'MEC', lambda: exige(
        # ⚠️ 27/09: «not about the family» repetia a oracao anterior e saiu; o alcance
        # continua dito por «no evaluated member clears it».
        # ⚠️ 27/09 (cli-3): a oracao saiu do texto (exemplo literal do parecer); o alcance
        # por membro avaliado continua na Tabela 5, «0 of 15 evaluated».
        [r'evaluated (implementations|operation)', r'\b\d+ of \d+ evaluated'], quantas=2)))
    P.append((21, 'leitura fluida', 'JUL', lambda: (True, 'conferido 22/09: sem pagina esparsa; roteiro da 4 na ordem real')))
    P.append((22, 'sem autodefesa forcada', 'MEC', lambda: proibe(
        [r'would serve', r'not ours to fix', r'no standing the others lack.{0,80}not ours'])))
    P.append((23, 'limitacoes no lugar certo', 'MEC', lambda: exige([r'\\subsection\{Limitations\}'])))
    P.append((24, 'explicacao x defesa', 'JUL', lambda: (True, 'conferido 22/09: 0 ocorrencias de «we do not»/«is not intended»')))
    P.append((25, 'resultado x interpretacao', 'MEC', lambda: exige(
        # ⚠️ 27/09: mesma ressalva do criterio 17, agora na 5.1.
        # ⚠️ 27/09 (cli-3): idem criterio 17.
        [r'consistent with .{0,40}and is not a demonstrated|remains a hypothesis|rests on alignment'])))
    P.append((26, 'sem repeticao', 'JUL', lambda: (True, 'guarda_sem_frase_repetida ✅: nenhuma afirmacao em duas secoes')))
    P.append((27, 'siglas por extenso', 'MEC', lambda: exige(
        [r'no-reference image quality assessment \(NR-IQA\)',
         r'Spearman Rank Correlation Coefficient \(SRCC\)'], quantas=2)))
    P.append((28, 'termos definidos', 'MEC', lambda: exige(
        [r'\\emph\{construct validity\}|\\emph\{Technical quality\}|construct validity\}?~\\citep',
         r'modular testbed'], quantas=2)))
    P.append((29, 'consistencia de nomes', 'JUL', lambda: (True, 'guarda_convencao_de_termos ✅ em 35 arquivos')))
    P.append((30, 'resumo e objetos autonomos', 'MEC', lambda: exige(
        [r'reads in greyscale', r'before ties\s+are removed'], quantas=2)))
    P.append((31, 'resumo < 250 palavras', 'MEC', lambda: (
        n_palavras_resumo() < 250, '%d palavras' % n_palavras_resumo())))
    P.append((32, 'resumo com argumento completo', 'MEC', lambda: exige(
        # ⚠️ 27/09 (cli-3): o resumo abre pela tese e diz «We test them in that role».
        [r'We (?:audit|test)', r'The study combines', r'Implementation choice is'], onde=r, quantas=3)))
    P.append((33, 'problema explicito', 'MEC', lambda: exige(
        # ⚠️ 27/09 (cli-3): o problema ficou mais explicito, nao menos: reuso SEM validacao.
        [r'may target appearance or\s+representativeness rather than technical quality'
         r'|reused to\s+rank those representatives by technical quality without validation'], onde=r)))
    P.append((34, 'contextualizacao suficiente', 'JUL', lambda: (True, 'conferido 22/09: P1 tem 60 palavras e ja chega a decisao')))
    P.append((35, 'fontes reais e pertinentes', 'MEC', lambda: exige([r'\\citep\{cronbach1955construct\}'])))
    P.append((36, 'lacuna demonstrada', 'MEC', lambda: exige(
        # ⚠️ 27/09: o padrao casava «what is absent is validation», que a limpeza do
        # tom defensivo reescreveu para «none validates». O FATO e o mesmo: a
        # lacuna continua demonstrada, e e ela que este criterio cobra.
        [r'[Aa]mong the sources verified here, (?:what is\s+absent|none validates)'])))
    P.append((37, 'importancia da contribuicao', 'MEC', lambda: exige(
        # ⚠️ 27/09 (cli-3): a frase da consequencia saiu da intro por repetir a tese, que
        # agora abre o segundo paragrafo e diz a consequencia para o pipeline.
        [r'can\s+change which representatives a pipeline preserves|which of them is used changes what the pipeline selects'])))
    P.append((38, 'proposta inequivoca', 'MEC', lambda: exige([r'The objective is to establish'])))
    P.append((39, 'objetivo x contribuicao x resultado', 'MEC', lambda: exige(
        [r'The study contributes \(i\)'])))
    P.append((40, 'objetivos verificaveis', 'MEC', lambda: exige([r'\(i\).{0,700}\(ii\).{0,700}\(iii\).{0,700}\(iv\)'])))
    # ⭐ 21/09: PROMOVIDO de JULGAMENTO para mecanico. Cada uma das quatro contribuicoes
    # declaradas tem de ter a subsecao de resultado que a sustenta; se uma sumir na
    # proxima reescrita, isto reprova em vez de eu reler e achar que esta la.
    P.append((41, 'contribuicao ligada a validacao', 'MEC', lambda: exige(
        [r'\\label\{sec:prov\}',            # (i)   proveniencia
         r'\\label\{sec:screen_results\}',  # (ii)  degradacao e associacao externa
         r'\\label\{sec:mechanism\}',       # (iii) decomposicao do BoVW
         r'\\label\{sec:menu\}'],           # (iv)  sensibilidade da selecao
        quantas=4)))
    # ⛔ 22/09: o criterio 42 ganhou a perna que FALTAVA. Depois da reescrita o corpo
    # dizia «whose interval excludes zero», «with both intervals positive» e «at a margin
    # this sample does not resolve» SEM IMPRIMIR os intervalos: as macros tinham sido
    # cortadas e a afirmacao ficou. ⭐ Afirmar que um intervalo exclui zero sem mostra-lo
    # e pior que omitir, porque o leitor nao tem como discordar — e nenhuma guarda pegava,
    # porque a frase-chave continua la e a frase-chave E a afirmacao.
    # 📌 A regra: quando a AFIRMACAO aparece, o NUMERO que a sustenta tem de aparecer.
    def afirmacao_com_numero():
        pares = [(r'interval (?:of [^ ]+ that )?excludes zero', r'\\vaIC\{\}'),
                 (r'margin\s+this sample does not resolve', r'\\koIC\{\}'),
                 # ⚠️ 22/09 (parecer v7, 2.1): a unidade primaria passou a ser o bloco
                 #    por fonte, entao o intervalo impresso e \finDovCas, nao o antigo.
                 (r'both intervals positive', r'\\(?:finDovCas|dovCasadoTopico)\{\}'),
                 (r'count within that\s+archive', r'\\cobMencoes\{\}'),
                 # ⛔ 22/09 (parecer v2): o corpo nao dizia a LATERALIDADE, e as 11
                 # celulas dependem dela — um bilateral simetrico nao rejeitaria nada.
                 (r'Holm over the', r'one-sided in the lower tail|one-sided \$p\$')]
        mudos = [a for a, n in pares
                 if re.search(a, todo, re.I) and not re.search(n, todo)]
        return (not mudos, 'nenhuma afirmacao sem o numero'
                if not mudos else 'AFIRMA SEM MOSTRAR: %s' % mudos)

    P.append((42, 'suficiencia da validacao', 'MEC', lambda: (
        exige([r'optimistic diagnostic', r'oracle-polarity diagnostic'], quantas=2)[0]
        and afirmacao_com_numero()[0],
        afirmacao_com_numero()[1])))
    P.append((43, 'decisao quando evidencia insuficiente', 'MEC', lambda: exige(
        # ⚠️ 22/09 (parecer v2, V2-089): a frase passou a separar o estudo pareado dos
        #    candidatos do estudo de preferencia entre resumos. O FATO exigido e o mesmo:
        #    dizer qual estudo decidiria o que esta em aberto.
        # ⛔ 22/09 (parecer v7, §3): «would settle» saiu do texto, e as TRES formas que
        #    esta entrada aceitava estavam mortas juntas — o criterio teria passado por
        #    uma redacao que o artigo nao tem mais. Fica a forma VIVA, conferida por
        #    grep nas secoes; se ela mudar de novo, o criterio reprova e obriga a reler
        #    se o FATO (dizer qual estudo decidiria o que esta em aberto) sobreviveu.
        [r'Three studies remain',
         r'would put the technical-quality ordering and a viewer'],
        quantas=2)))
    P.append((44, 'fluxo da introducao', 'JUL', lambda: (True, 'conferido 22/09: 6 paragrafos, contexto->problema->lacuna->desenho->objetivo->contribuicoes')))
    # ⛔ 22/09 (parecer v2, V2-042): a ancora era o ROTEIRO de sete blocos, e o parecer
    # mandou encurta-lo por repetir o que os titulos ja dizem. ⚠️ Um checklist que exige o
    # que a rubrica proibe deixa de ser controle e vira ancora do defeito: a evidencia do
    # criterio passa a ser a transicao que liga o desenho ao que os resultados mostram.
    P.append((45, 'metodo e resultados respondem', 'JUL', lambda: (True,
        'conferido 25/09: as sete subsecoes de resultados respondem, na ordem, ao que o '
        'metodo monta — classes/testbed, degradacao controlada, mecanismo, compostos, '
        'validacao externa e triagem, efeito na selecao, sintese por fonte')))
    P.append((46, 'conclusao responde aos objetivos', 'MEC', lambda: exige(
        # ⚠️ 22/09: a reescrita do parecer v3 abre com «This study evaluated» e fecha
        #    com «The results are bounded by». A afirmacao exigida e a mesma.
        # ⚠️ 27/09 (cli-3): a conclusao abre pela resposta, nao pela pergunta.
        [r'This study (?:examined|evaluated|asked)|reused as standalone\s+technical-quality scores, fail in that role',
         r'The (?:evidence|results) (?:is|are) bounded by'], quantas=2)))
    P.append((47, 'mesmo alcance resumo/intro/conclusao', 'MEC', lambda: proibe(
        [r'the field uses measure', r'Read by class rather than by operation'])))
    P.append((48, 'concisao por precisao', 'JUL', lambda: (True, 'texto -38%; as 7 perdas que as guardas acusaram foram REPOSTAS')))
    return P


def autoteste():
    """⛔ SEM ESTA PERNA O CHECKLIST E TEATRO. Ela planta o mundo errado em tres eixos e
    exige reprovacao: (a) uma formulacao PROIBIDA de volta, (b) uma frase EXIGIDA fora,
    (c) um resumo acima do limite. Se algum passar, o criterio correspondente nao mede
    nada. Ver [[controle-positivo-que-nao-pode-falhar]]."""
    import builtins
    orig_corpo, orig_resumo = globals()['corpo'], globals()['resumo']
    falhas = []

    # (a) a frase que o parecer mandou remover volta: o criterio 4 tem de cair
    globals()['corpo'] = lambda: orig_corpo() + \
        '\nthe three classes the field uses measure a count of local detail.\n'
    if all(f()[0] for n, _, _, f in checagens() if n == 4):
        falhas.append('criterio 4 nao reprova a formulacao proibida de volta')
    globals()['corpo'] = orig_corpo

    # (b) a frase exigida sai: o criterio 38 tem de cair
    globals()['corpo'] = lambda: orig_corpo().replace('The objective is to establish', 'We look at')
    if all(f()[0] for n, _, _, f in checagens() if n == 38):
        falhas.append('criterio 38 nao reprova a ausencia da proposta')
    globals()['corpo'] = orig_corpo

    # (c) resumo estourado: o criterio 31 tem de cair
    globals()['resumo'] = lambda: orig_resumo() + ' palavra' * 300
    if all(f()[0] for n, _, _, f in checagens() if n == 31):
        falhas.append('criterio 31 nao reprova um resumo de 500 palavras')
    globals()['resumo'] = orig_resumo

    for x in falhas:
        print('  ⛔ AUTOTESTE: %s' % x)
    if not falhas:
        print('  autoteste ✅ (formulacao proibida, proposta ausente e resumo estourado REPROVAM)')
    return not falhas


def main():
    if not autoteste():
        return 1
    P = checagens()
    mec = jul = 0
    ruins = []
    for n, nome, tipo, f in P:
        ok, ev = f()
        if tipo == 'MEC':
            mec += ok
        else:
            jul += 1
        if not ok:
            ruins.append((n, nome, ev))
        print('  %s %2d %-42s %s' % ('✅' if ok else '⛔', n, nome[:42], ev[:52]))
    n_mec = sum(1 for x in P if x[2] == 'MEC')
    print('\n  %d criterios: %d mecanicos (%d passam), %d de julgamento'
          % (len(P), n_mec, mec, jul))
    if ruins:
        print('  ⛔ NAO CUMPRIDOS:')
        for n, nome, ev in ruins:
            print('     %2d %s -> %s' % (n, nome, ev))
    else:
        print('  ✅ os 48 cumpridos (os de julgamento com a evidencia apontada)')
    return 0 if not ruins else 1


if __name__ == '__main__':
    sys.exit(main())
