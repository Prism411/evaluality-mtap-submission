#!/usr/bin/env python3
"""⭐ SINCRONIZA OS PONTEIROS DO CORPO PARA O SUPLEMENTAR, a partir do que o LaTeX produziu.

POR QUE EXISTE (07/09/2026). Sao dois documentos separados, entao `\\ref` nao alcanca: o corpo
cita tabela do suplementar pelo NUMERO DIGITADO. E o numero muda toda vez que uma tabela entra
ou sai do suplementar. Isso aconteceu TRES vezes numa noite:
  - inserir a `tab_ct`  empurrou o rastreio de S17 para S18;
  - mover a `tab_screening` empurrou tudo de novo;
  - mover a `tab_e2e` empurrou pela terceira vez.
Nas tres o corpo continuou apontando para o numero velho, que EXISTIA — apontando para outra
tabela. Consertar a mao nao escala e ja errei uma vez.

COMO FUNCIONA: cada entrada liga um rotulo a um TRECHO do corpo que o cita. O script le o
`supplementary.aux`, acha o numero real e reescreve o numero na frase daquele trecho.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
CORPO = ['main.tex', 'sec_intro.tex', 'sec_related.tex', 'sec_method.tex',
         'sec_results.tex', 'sec_discussion.tex', 'sec_conclusion.tex']

# rotulo -> trecho do corpo, unico, que contem o ponteiro daquele rotulo
ANCORA = {
    # ⛔ RECONSTRUIDO em 21/09/2026, depois da reescrita que cortou o corpo de 11085 para
    # ~6800 palavras. A reescrita quebrou DEZENOVE ancoras de uma vez: as frases que elas
    # casavam deixaram de existir, e o sincronizador acusou. ⭐ Sem essa acusacao, dezenove
    # ponteiros para o suplementar ficariam «certos por acaso», envelhecendo calados na
    # proxima vez que uma tabela mudasse de numero.
    # ⚠️ As entradas cujo PONTEIRO saiu do corpo foram REMOVIDAS, nao atualizadas: entrada
    # morta tem de reprovar, e nao ficar de reserva esperando a frase voltar.
    'fig:inversion': 'are wrong on all 100 noise pairs',  # 27/09 (cli-3): frase reescrita
    'fig:mechanism': 'not repair the reading either',
    'fig:jusante': 'the same swaps rewrite much of the stage output',
    # ⚠️ 22/09 (reescrita do parecer v3): a frase virou «identifies coverage per analysis».
    'tab:coverage': 'gives the coverage of each analysis',  # 27/09 (cli-3)
    # ⚠️ 22/09 (parecer v5, 2.3): a frase passou a falar das DUAS formulacoes, entao
    #    «of it» virou «of them». O ponteiro e o fato apontado sao os mesmos.
    'tab:ct': 'concern the formulations as published',  # 27/09 (cli-3)
    'tab:degradation': 'of the 19 operational topics',
    # ⚠️ 22/09 (parecer v5, §3): a frase saiu de «the retention percentages above use»
    #    para «The two sets of retention percentages come from different regimes».
    'tab:e2e': 'scores each complete operation',
    # ⚠️ 22/09 (parecer v6, 2.2): «were collected» dava as configuracoes como
    #    publicadas; a frase passou a dizer como elas foram montadas.
    'tab:compostos': 'attribute configurations combine the implemented statistics',
    # ⭐ 22/09 (parecer v2, V2-050): a frase dos dezassete nao dizia onde eles estao.
    # ⚠️ 22/09 (parecer v7, 2.4): a frase passou a identificar a populacao dos
    #    dezessete, e o ponteiro mudou de lugar dentro dela.
    'tab:literature': 'lists the operations that meet it',
    # ⭐ 23/09 (parecer v8, §3): a promessa «o suplementar registra os dezessete»
    #    nao tinha ponteiro, e o revisor procurou o registro e nao achou.
    'tab:dezessete': 'records the literature operations with their',
    'tab:inventory': 'states the objective and role recorded for each',
    'tab:methods_supp': 'the 19-extractor ablation, are in',  # 27/09 (cli-3)
    'tab:preds_supp': 'including the two overlay predictions, is in',
    'tab:protocolo': 'limits of that instrument are recorded in',
    'tab:taxonomy_works': 'work by work in',
    'tab:threshold_sens': 'Threshold sensitivity is reported in',
    'tab:trace': 'adaptations are recorded separately in',
}


def _padrao(trecho):
    r"""⛔ 21/09: o casamento era `re.escape(trecho)` sobre o texto CRU, entao uma ancora
    cuja frase o LaTeX quebrou em duas linhas NAO casava, e aquele ponteiro simplesmente
    deixava de ser sincronizado, sem nada reprovar. Eram TRES das trinta. O espaco em
    branco da ancora passa a casar qualquer espaco, inclusive quebra de linha."""
    return r'\s+'.join(re.escape(x) for x in trecho.split())


def _sem_chave_repetida():
    """⛔ 14/09: `tab:validation` entrou duas vezes e a segunda apagou a primeira em
    silencio, deixando um ponteiro do corpo sem sincronizacao nenhuma. Um dict literal
    nao reclama; esta leitura da FONTE reclama."""
    fonte = Path(__file__).read_text()
    i = fonte.find('ANCORA = {'); j = fonte.find('\n}', i)
    ks = re.findall(r"^\s*'([^']+)':", fonte[i:j], re.M)
    dup = sorted({k for k in ks if ks.count(k) > 1})
    if dup:
        raise SystemExit('⛔ chave repetida em ANCORA, a primeira e perdida: %s' % dup)
    return len(ks)


def numeros():
    a = (AQUI / 'supplementary.aux').read_text()
    return {m.group(1): m.group(2) for m in
            re.finditer(r'\\newlabel\{([^}]*)\}\{\{(S\d+)\}', a)}


def maior_tabela():
    a = (AQUI / 'supplementary.aux').read_text()
    n = [int(x) for x in re.findall(r'\\newlabel\{tab:[^}]*\}\{\{S(\d+)\}', a)]
    return max(n) if n else 0


def maior_figura():
    """O maior S de FIGURA no suplementar, lido do .aux que o LaTeX produziu."""
    n = [int(x) for x in re.findall(r'\\newlabel\{fig:[^}]*\}\{\{S(\d+)\}',
                                   (AQUI / 'supplementary.aux').read_text())]
    return max(n) if n else 0


def _inicio_da_janela(s, ini):
    """Onde a janela de uma ancora comeca: o ponto final antes de `ini - 200`,
    MAS nunca antes do paragrafo em que a ancora esta.

    ⛔ 27/09: sem o limite de paragrafo a janela atravessava a linha em branco e
    engolia o fim do paragrafo anterior. Foi assim que `tab:inventory`, cuja
    frase abre um paragrafo novo, passou a ter o `Table~S30` do paragrafo de
    cima dentro da janela: o ponteiro MAIS PROXIMO da ancora virava o da outra
    tabela, e cada passada reescrevia um numero certo com o numero errado.
    ⭐ Ponteiro de OUTRO paragrafo nunca e o ponteiro desta frase.
    """
    a = s.rfind('.', 0, max(0, ini - 200)) + 1
    par = s.rfind('\n\n', 0, ini)
    return max(a, par + 2) if par >= 0 else a


def _janelas_nao_colidem():
    """Duas ancoras diferentes na MESMA janela fazem o numero de uma sobrescrever o da
    outra a cada passada. O sintoma e nao convergir; a causa e a distancia no texto."""
    num = numeros()
    for nome in CORPO:
        p = AQUI / nome
        if not p.exists():
            continue
        s = p.read_text()
        vistos = []
        for rot, trecho in ANCORA.items():
            if not num.get(rot.split('#')[0]):
                continue
            for m in re.finditer(_padrao(trecho), s):
                a = _inicio_da_janela(s, m.start())
                b = s.find('.', m.end())
                vistos.append((a, b if b > 0 else len(s), rot))
        vistos.sort()
        for (a1, b1, r1), (a2, b2, r2) in zip(vistos, vistos[1:]):
            if a2 < b1 and r1.split('#')[0] != r2.split('#')[0]:
                raise SystemExit(
                    '⛔ %s: as ancoras de %s e %s caem na mesma janela, entao cada passada '
                    'reescreve o numero de uma com o da outra. Separe os dois ponteiros em '
                    'paragrafos diferentes.' % (nome, r1, r2))


def _sem_ancora_morta():
    """⛔ 21/09: TODA ancora tem de casar ao menos uma frase do corpo.

    A de `fig:inversion` estava morta: a frase foi reescrita e a ancora ficou com a
    redacao antiga. Enquanto o numero da figura nao se mexeu, ninguem percebeu — o
    ponteiro continuava certo por acaso. Ao subir a figura do menu para o corpo, a de
    inversao passou de S4 para S3 e o corpo ficou apontando para a figura ERRADA, sem
    nada reprovar, porque o sincronizador simplesmente nao encontrava onde reescrever.

    ⭐ Ancora morta nao e ruido: e um ponteiro que deixou de ser mantido e que vai
    envelhecer calado na primeira vez que a numeracao andar.
    """
    s = '\n'.join((AQUI / n).read_text() for n in CORPO if (AQUI / n).exists())
    num = numeros()
    mortas = sorted(rot for rot, trecho in ANCORA.items()
                    if num.get(rot.split('#')[0]) and not re.search(_padrao(trecho), s))
    # ⚠️ A DIVIDA CONHECIDA FICA CONGELADA AQUI, nao escondida. Estas dez ja estavam
    # mortas antes de 21/09 e cada uma precisa de leitura da frase que a substituiu, o que
    # nao se faz em bloco sem arriscar apontar para a tabela errada. ⛔ Mas nenhuma NOVA
    # pode entrar: a lista e o teto, e ultrapassa-lo reprova.
    # ⭐ 21/09, fim: a divida foi a ZERO. As dez ancoras mortas foram resolvidas uma a
    # uma contra a frase que de fato cita o rotulo: cinco ganharam a redacao atual e
    # cinco SAIRAM, porque o rotulo delas nao tem ponteiro individual no corpo e nao
    # havia o que sincronizar. A lista fica vazia de proposito: ancora morta reprova.
    CONHECIDAS = set()
    novas = [r for r in mortas if r not in CONHECIDAS]
    curadas = sorted(CONHECIDAS - set(mortas))
    if curadas:
        raise SystemExit(
            '⛔ %d ancora(s) da divida conhecida voltaram a casar: %s. Tire-as de '
            'CONHECIDAS, senao a lista vira teto que nunca baixa.' % (len(curadas),
                                                                      ', '.join(curadas)))
    if mortas:
        print('  ⚠️  %d ancora(s) nao casam frase nenhuma do corpo (divida conhecida): %s'
              % (len(mortas), ', '.join(mortas)))
    if novas:
        raise SystemExit(
            '⛔ %d ancora(s) NOVAS nao casam frase nenhuma do corpo: %s. A frase foi '
            'reescrita e '
            'a ancora ficou para tras; o ponteiro dela nao e mais sincronizado e so esta '
            'certo por acaso.' % (len(novas), ', '.join(novas)))


def sincroniza(escreve=True):
    _sem_chave_repetida()
    _sem_ancora_morta()
    _janelas_nao_colidem()          # o dict ja perdeu a chave; a fonte ainda sabe
    num, trocas = numeros(), []
    for nome in CORPO:
        p = AQUI / nome
        if not p.exists():
            continue
        s = orig = p.read_text()
        for rot, trecho in ANCORA.items():
            alvo = num.get(rot.split('#')[0])
            if not alvo:
                continue
            for m in re.finditer(_padrao(trecho), s):
                # a frase inteira em volta do trecho, para achar o ponteiro dela
                a = _inicio_da_janela(s, m.start())
                b = s.find('.', m.end())
                frase = s[a:b + 1] if b > 0 else s[a:]
                # ⛔ 21/09: aqui a substituicao era `re.sub` sobre a JANELA INTEIRA, e a
                # janela comeca no minimo 200 caracteres ANTES do trecho, entao ela
                # engole a frase anterior. Quando a ancora `tab:e2e#2` («scores each»)
                # passou a ter a frase da cobertura na janela, o `Table~S18` dela foi
                # reescrito para S19: um ponteiro CERTO corrompido pela sincronizacao de
                # outro. ⭐ Agora so o ponteiro MAIS PROXIMO do trecho e reescrito.
                alvos = list(re.finditer(r'((?:Table|Tables|Fig\.|Figure)~?)S\d+', frase))
                nova = frase
                if alvos:
                    rel = m.start() - a
                    q = min(alvos, key=lambda x: min(abs(x.start() - rel),
                                                     abs(x.end() - rel)))
                    nova = frase[:q.start()] + q.group(1) + alvo + frase[q.end():]
                if nova != frase:
                    s = s[:a] + nova + s[b + 1:] if b > 0 else s[:a] + nova
                    trocas.append((nome, rot, alvo))
        # As faixas guarda-chuva acompanham o maior numero real de CADA familia.
        # ⛔ Ate 08/09 esta linha trocava QUALQUER `S1--SN` pelo maior numero de TABELA, e
        # por isso reescreveu «Supplementary Figures S1--S4» como «S1--S26». A familia
        # agora entra no padrao, e cada uma le o seu proprio maximo.
        for palavra, maior in (('Tables', maior_tabela()), ('Figures', maior_figura())):
            alvo_faixa = f'{palavra} S1--S{maior}'
            s2 = re.sub(palavra + r'\s+S1\s*-{2,}\s*S\d+', alvo_faixa, s)
            if s2 != s:
                trocas.append((nome, 'faixa ' + palavra, alvo_faixa))
                s = s2
        if s != orig and escreve:
            p.write_text(s)
    return trocas


def _autoteste():
    """⭐ Duas pernas: rodar de novo nao muda nada, e um numero errado E corrigido."""
    sincroniza()
    assert not sincroniza(), '⛔ nao converge: a segunda passada ainda muda algo'
    p = AQUI / 'sec_method.tex'
    antes = p.read_text()
    num = numeros()['tab:trace']
    # ⚠️ 21/09: o autoteste plantava o erro em «Table~S22 documents each implementation»,
    #    frase que a reescrita do corpo trocou. O controle deixou de plantar coisa alguma
    #    e passou a falhar por nao achar o alvo — controle preso a uma redacao.
    #    ⭐ Agora o alvo sai do PROPRIO texto: a primeira ocorrencia do ponteiro.
    import re as _re
    # ⛔ 22/09: plantar na PRIMEIRA ocorrencia do numero era fragil. Uma frase nova citou
    #    a mesma tabela ANTES da frase-ancora, o controle plantou fora da janela e o
    #    autoteste reprovou uma sincronizacao correta. ⭐ O alvo agora e o ponteiro que
    #    segue a ANCORA, que e exatamente o que esta funcao sincroniza.
    _anc = _re.search(_padrao(ANCORA['tab:trace']), antes)
    assert _anc, '⛔ a ancora de tab:trace sumiu do corpo: nao ha o que plantar'
    _rel = _re.search(r'Table~%s\b' % num, antes[_anc.end():])
    assert _rel, '⛔ o ponteiro de tab:trace sumiu do corpo: nao ha o que plantar'
    _ini, _fim = _anc.end() + _rel.start(), _anc.end() + _rel.end()
    p.write_text(antes[:_ini] + 'Table~S99' + antes[_fim:])
    t = sincroniza()
    assert any(r == 'tab:trace' for _, r, _ in t), '⛔ nao corrigiu o ponteiro quebrado'
    assert p.read_text() == antes, '⛔ nao restaurou exatamente o valor certo'
    return True


if __name__ == '__main__':
    assert _autoteste()
    t = sincroniza()
    print(f'  autoteste ✅ (corrige um S99 plantado e converge)')
    print(f'  {len(t)} ponteiro(s) sincronizado(s)' if t else '  ✅ ja estavam todos certos')
    for f, r, n in t:
        print(f'    {f}: {r} -> {n}')
    for rot, n in sorted(numeros().items()):
        if rot in ANCORA:
            print(f'    {rot:<16} = {n}')
    sys.exit(0)
