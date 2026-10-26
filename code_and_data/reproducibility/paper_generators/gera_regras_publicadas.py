#!/usr/bin/env python3
"""As macros da secao que fecha «os modulos nao foram reproduzidos como publicados».

Cada fonte que ESPECIFICA uma regra de combinacao teve essa regra implementada e medida na
mesma bancada pareada. Nada aqui e escolha nossa de agregacao: e o que o PDF manda fazer.
"""
import os
import json
import re
from pathlib import Path


# ⛔ `` comia o zero INTERNO: 40.5 virava 4.5.
# Tira so o zero a esquerda do ponto que nao vem depois de digito.
def sem_zero(t):
    return re.sub(r'(?<![0-9])0\.', '.', t)


def sci(v, casas=2):
    """Notacao cientifica como artigo escreve, nao como Python imprime."""
    m, e = ('%.*e' % (casas, v)).split('e')
    return r'%s\times 10^{%d}' % (m, int(e))


def ic(par, casas=3):
    """Um intervalo na convencao do artigo: sem zero a esquerda e com menos.

    ⛔ 27/09 (parecer): os intervalos da 4.5 saiam «[0.273, 0.792]» e «[-0.302,
    0.420]», com zero a esquerda e HIFEN, enquanto o resto do artigo escreve
    «.551» e «$-$». Eram dois formatos para a mesma coisa na mesma pagina.
    """
    def um(v):
        t = sem_zero('%.*f' % (casas, v))
        return ('$-$' + t[1:]) if t.startswith('-') else t
    return '[%s, %s]' % (um(par[0]), um(par[1]))


import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminho_dos_dados import DADOS as QB   # noqa: E402
SAIDA = Path(__file__).parent / 'regras_publicadas.tex'


def sem_zero_negativo(x):
    # ⛔ negar um 0.0 produz -0.0, e o PDF saia com «[-0.0, 10.6]». O valor da
    # fonte e exatamente zero; o sinal e artefato da negacao.
    v = -x
    return 0.0 if v == 0 else v


POREXT = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six',
          7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven',
          12: 'twelve', 13: 'thirteen', 14: 'fourteen', 15: 'fifteen',
          16: 'sixteen', 17: 'seventeen', 18: 'eighteen', 19: 'nineteen',
          20: 'twenty', 21: 'twenty-one', 22: 'twenty-two'}


def main():
    ke = json.load(open(QB / 'o_classificador_do_ke_recupera.json'))['ACURACIA']
    sr = json.load(open(QB / 'a_regra_que_o_srinivas_especifica.json'))
    qa = json.load(open(QB / 'onde_cada_termo_do_qaroush_entra.json'))
    ct = json.load(open(QB / 'o_CT_do_qaroush_inverte_por_construcao.json'))
    au = json.load(open(QB / 'quantas_sao_indice_autonomo_na_fonte.json'))
    val = json.load(open(QB / 'o_que_cada_fonte_valida.json'))
    prov = json.load(open(QB / 'a_proveniencia_fecha_com_a_bib.json'))
    sub = json.load(open(QB / 'a_substituicao_concorda_acima_do_acaso.json'))
    inv = json.load(open(QB / 'quantas_invertem_ALEM_DO_ACASO.json'))
    fus = json.load(open(QB / 'a_fusao_de_fontes_vale_na_aplicacao.json'))
    fin = json.load(open(QB / 'a_fusao_nas_inferencias_da_aplicacao.json'))
    srf = json.load(open(QB / 'o_surf_esta_fora_por_licenca.json'))
    dez = json.load(open(QB / 'quem_sao_os_dezessete.json'))
    blo = json.load(open(QB / 'o_binomial_respeita_o_bloco.json'))
    top = json.load(open(QB / 'o_bloco_de_topico_e_a_unidade_mais_alta.json'))
    # ⭐ 21/09 (parecer, D02 e E23): a energia de alta frequencia era INTERPRETADA na
    # discussao sem que a medida aparecesse antes. Ela existe, medida, e passa a
    # entrar por macro no corpo, onde o fato descritivo pertence.
    ene = json.load(open(QB / 'energia_por_tipo.json'))['energia_por_tipo']
    mch = json.load(open(QB / 'o_bloco_de_segmento_reproduz_um_intervalo_publicado.json'))['manchete']
    exc = json.load(open(QB / 'as_tres_excecoes_do_mecanismo.json'))
    tab4 = json.load(open(QB / 'a_tabela_4_reproduz.json'))['por_metodo']
    AQ = Path(__file__).parent
    r2 = json.load(open(AQ / 'second_revision_reanalysis.json'))['application']['branches']
    r3 = json.load(open(AQ / 'third_revision_reanalysis.json'))['same_frame_same_pooling']
    # ⛔ 14/09: o corpo dizia «the same ten frames»; o regime e capped10 e a media
    #    comum medida e 9,98, entao o numero certo e o TETO, nao a contagem.
    r3s = json.load(open(AQ / 'third_revision_reanalysis.json'))['same_frame_same_pooling']['sampling_summary']
    tec = r2['technical']['liqe_minus_sift']
    cas = r3['regimes']['uniform_1fps_capped10_mean']['liqe_minus_sift']
    # ⛔ 21/09: `\escMedia` e `\escGrandes` saiam de `quantas_escolhas_distintas_por_cluster`
    # (14 operacoes), e a frase que os usa fica num paragrafo cujo sujeito passou a ser 21.
    # Repontado para a mesma fonte da manchete. ⭐ E o valor NAO MUDA em campo nenhum
    # (2,21 · 6 · 6 · 42 nos dois), porque os agrupamentos ja saturavam com 14: acrescentar
    # operacoes nao tem como aumentar a dispersao depois que todo candidato ja e escolhido.
    esc = json.load(open(QB / 'quantos_resumos_distintos_a_classe_produz.json'))
    eff = json.load(open(QB / 'posto_e_m_eff_das_15.json'))
    ref = json.load(open(QB / 'a_sensibilidade_depende_de_quais_referencias.json'))
    cas3 = json.load(open(QB / 'o_casamento_sozinho_move_doze.json'))
    mcb = json.load(open(QB / 'o_mcnemar_dos_42_com_topico_como_unidade.json'))
    # ⭐ 12/09: o protocolo de identificacao das operacoes existia em disco desde 05/09 e
    # nunca entrou no artigo. Um revisor cobrou justamente isso.
    acv = json.load(open(QB / 'o_que_os_173_usam_no_lugar.json'))
    _red = json.load(open(QB / 'a_reducao_no_regime_implantado.json'))
    from collections import Counter as _C
    _q15 = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    _bp = _C('KADID' if v['kadid_global'] <= v['koniq_global'] else 'KonIQ'
             for k, v in _q15.items() if k != 'si')
    assert sum(_bp.values()) == 15, _bp
    vrr = json.load(open(QB / 'a_varredura_sem_a_bibliografia.json'))
    cob = json.load(open(QB / 'as_15_do_artigo_cobrem_o_que_o_campo_usa.json'))
    acc = json.load(open(QB / 'o_acervo_com_o_varredor_consertado.json'))
    pd2 = json.load(open(QB / 'o_piso_das_duas_familias_na_mesma_convencao.json'))
    mtip = json.load(open(QB / 'a_manchete_depende_de_quais_tipos.json'))['por_cenario']
    rei = json.load(open(QB / 'a_reimplementacao_reproduz_a_falha.json'))
    par = json.load(open(QB / 'a_contagem_reproduz_a_escolha_par_a_par.json'))
    cla = json.load(open(QB / 'a_classe_nao_concorda_consigo.json'))
    # ⛔ 25/09 (parecer v9, §1.1): `a_implantada_e_tipica_da_classe.json` esta na regua
    # RIVAL (decisiva, tipos alinhados fora). Os tres numeros publicados batiam por
    # coincidencia; o minimo e o maximo dele NAO batem. Passa a sair da regua canonica,
    # a mesma da Tabela 6, e a coincidencia vira CONTROLE em vez de sorte.
    _tipc = json.load(open(QB / 'os_dezessete_na_regua_da_tabela6.json'))
    _tipr = json.load(open(QB / 'a_implantada_e_tipica_da_classe.json'))['classe_de_sumarizacao']
    tip = {'classe_de_sumarizacao': {
        'n': _tipc['dezessete']['n'],
        'quantas_ficam_abaixo_da_implantada': _tipc['dezessete']['abaixo'],
        'mediana': _tipc['dezessete']['mediana']}}
    for _k in ('n', 'quantas_ficam_abaixo_da_implantada', 'mediana'):
        assert abs(tip['classe_de_sumarizacao'][_k] - _tipr[_k]) < 0.05, (
            '⛔ as duas reguas deixaram de concordar em %r (%s x %s). O corpo publica o '
            'valor CANONICO; se ele mudou, a frase dos dezessete precisa ser relida.'
            % (_k, tip['classe_de_sumarizacao'][_k], _tipr[_k]))
    ele = json.load(open(QB / 'a_elegibilidade_e_familia_nao_supervisao.json'))
    comb = json.load(open(QB / 'as_combinacoes_COMO_A_LITERATURA_PUBLICA.json'))
    _q = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))
    q15, regra = _q['por_operacao'], _q['regra']
    # ===================================================================
    # ⭐ insumos do RESUMO GRAFICO, medidos aqui para a peca nao digitar nada.
    # ===================================================================
    # ⛔ o filtro do `si` NAO e detalhe: o arquivo tem 16 entradas e o artigo
    # fala de 15. Ancorado na proveniencia, nao num 15 literal, para que trocar
    # o corpus reprove aqui em vez de imprimir o denominador errado na figura.
    _tri15 = {k: v for k, v in q15.items() if k != 'si'}
    assert len(_tri15) == prov['n_operacoes_das_15'], (
        '⛔ tirando o `si` sobraram %d operacoes, e a proveniencia diz %d: o '
        'resumo grafico imprimiria o denominador errado.'
        % (len(_tri15), prov['n_operacoes_das_15']))
    _tri_passam = sum(1 for v in _tri15.values() if v['elegivel'])
    # ⚠️ zero esperado AQUI e o achado, nao bug: nenhuma das 15 passa as duas
    # condicoes. Declarado, para nao passar por engano se a fonte vier vazia.
    assert all('elegivel' in v for v in _tri15.values()), \
        '⛔ alguma das 15 nao tem veredito de elegibilidade'
    _tri_nomes = ' $\\cdot$ '.join(
        n.replace('+', '$+$') for n in sorted(ele['elegiveis']))
    _pq = json.load(open(QB / 'a_contagem_reproduz_o_piso_do_artigo.json'))['⭐_por_quantidade']
    _piso, _piso_op = _pq, _pq['score publicado (a operacao)']
    assert _piso_op['de'] == _pq['MODELO liqe']['de'], (
        '⛔ o piso do SIFT+BoVW e o do LIQE nao tem o mesmo denominador')
    _red_rho = json.load(open(QB / 'a_reducao_no_regime_implantado.json'))[
        'correlacao_com_o_score_publicado']['n_desc']['spearman_com_bovw_sum']
    _tri_bases = len(json.load(
        open(QB / 'a_correlacao_com_a_contagem_por_base.json'))['por_base'])
    # o «800» da peca: 20 segmentos x 8 tipos x 5 niveis, contados do arquivo
    _pa = json.load(open(QB / 'ops_da_literatura_designA.json'))
    _pa_seg = len(_pa['por_segmento'])
    _pa_tipos = len(next(v for v in _pa['resumo_designA'].values()
                         if 'ordem' in v)['ordem'])
    _pa_niveis = len([k for k in next(iter(next(iter(
        _pa['por_segmento'].values())).values())) if k.startswith('blur_')])
    # ⭐ o painel 1: inversores por tipo. O universo aqui e o CERTO -- o
    # `quantas_invertem_ALEM_DO_ACASO.json` traz exatamente as 15 com direcao
    # declarada, sem o `si` e sem as tres que a origem nao orienta.
    _ROTULO = {'noise': 'Noise', 'satur': 'Saturation', 'blur': 'Blur',
               'h264': 'H.264', 'jpeg': 'JPEG', 'rescale': 'Rescale',
               'dark': 'Darken', 'motion': 'Motion'}
    assert len(inv['por_operacao']) == prov['n_operacoes_das_15'], (
        '⛔ o arquivo das inversoes tem %d operacoes, nao as %d do artigo'
        % (len(inv['por_operacao']), prov['n_operacoes_das_15']))
    _inv_conta = {t: sum(1 for v in inv['por_operacao'].values()
                         if (lambda a: a is not None and a < 50)(
                             v['acuracia_por_tipo'].get(t)))
                  for t in _ROTULO}
    # ⚠️ ordem por contagem e depois pelo nome: sem o desempate o .tex mudaria
    # de forma entre rodadas e a guarda de determinismo reprovaria.
    _inv_lista = ', '.join(
        '%s/%d' % (_ROTULO[t], n) for t, n in
        sorted(_inv_conta.items(), key=lambda kv: (-kv[1], kv[0])))
    assert max(_inv_conta.values()) == int(
        sum(1 for v in inv['por_operacao'].values()
            if (lambda a: a is not None and a < 50)(
                v['acuracia_por_tipo'].get('noise')))), \
        '⛔ o ruido deixou de ser o tipo com mais inversoes: reler o painel 1'
    # o denominador dos modelos dedicados: a MESMA fonte que alimenta a macro
    # de prosa \\invModelos, para os dois nunca divergirem
    _inv_mod_n = inv['a_outra_familia']['n_modelos']
    _dis_grupos = ','.join(
        str(len(g)) for g in sorted(
            json.load(open(QB / 'quantos_resumos_distintos_a_classe_produz.json')
                      )['todas_as_operacoes']['grupos'].values(),
            key=lambda g: (-len(g), g[0])))
    assert _pa_niveis == 5 and _pa_tipos == 8 and _pa_seg == 20, (
        '⛔ o desenho A mudou de forma: %d segmentos x %d tipos x %d niveis'
        % (_pa_seg, _pa_tipos, _pa_niveis))
    va = json.load(open(QB / 'o_vascore_do_qaroush_como_a_Eq20_manda.json'))
    ko = json.load(open(QB / 'o_modulo_do_korolkov_nos_11_segmentos.json'))
    # ⛔ 21/09: as macros `dup*` saiam de `a_concordancia_sem_as_duplicatas.json` (07/09),
    # medido sobre 14 operacoes, enquanto a manchete de 4.6 e o resumo ja falavam em 21.
    # O corpo carregava os DOIS universos para a mesma pergunta e nada os reconciliava.
    # Passam a sair do mesmo arquivo da manchete, que cobre as 21. ⚠️ As 14 eram
    # subconjunto estrito das 21, entao e re-tabulacao do material arquivado.
    _dz = json.load(open(QB / 'quantos_resumos_distintos_a_classe_produz.json'))
    if not _dz.get('controle_passou'):
        raise SystemExit('⛔ o controle das identidades declaradas REPROVOU na fonte')
    du = {'piso_do_acaso_pct': _dz['piso_do_acaso_pct'],
          'com_duplicatas': {'n_pares': _dz['par_a_par']['n_pares'],
                             'mediana': _dz['par_a_par']['mediana_pct'],
                             'abaixo_do_acaso': _dz['par_a_par']['abaixo_do_piso']},
          'sem_duplicatas': {'n_pares': _dz['par_a_par_colapsado']['n_pares'],
                             'mediana': _dz['par_a_par_colapsado']['mediana_pct'],
                             'abaixo_do_acaso': _dz['par_a_par_colapsado']['abaixo_do_piso']}}
    ct2 = json.load(open(QB / 'o_contraste_pareado_dos_modulos.json'))
    # ⚠️ estas macros viviam na tab_literatura.tex, que foi para o suplementar; o corpo
    # perdeu as definicoes e o build quebrou em 7 pontos. Vivem aqui agora.
    # ⭐ 21/09/2026, decisao do [author]: o piso passa a sair da BANCADA UNICA.
    # O arquivo anterior cobria 11 operacoes e, dessas, onze eram pontuadas com um
    # decodificador de quadro DIFERENTE do da referencia, enquanto o `si` e cinco
    # outras usavam o mesmo. `o_piso_numa_bancada_so.json` pontua TODAS com o
    # decodificador da referencia, nos mesmos 83 segmentos dos 42 clusters, com a
    # mesma aritmetica de kappa e o mesmo bootstrap por bloco de topico (semente 42).
    # ⭐ NENHUM veredito publicado muda de lado; a maior mudanca de kappa vale tres
    # clusters de concordancia, e as operacoes que se movem sao as de margem abaixo
    # da mediana, ou seja desempate no passo de discretizacao.
    # ⚠️ O que MUDA e a POPULACAO: de dez operacoes para as dezesseis auditadas.
    _pz = json.load(open(QB / 'o_piso_numa_bancada_so.json'))['por_operacao']
    tab16 = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    # o formato do arquivo novo nomeia os campos sem sufixo; adapta-se aqui, uma vez
    pz = {k: {'operacao': k,
              'kappa': v['kappa_numa_bancada_so'],
              'ic_inferior': v['ic_inferior_numa_bancada_so'],
              'passa': v['passa_numa_bancada_so']}
          for k, v in _pz.items()}
    # ⛔ o `qaroush_ct` ganhou piso nesta rodada mas NUNCA fez parte das dezesseis
    # auditadas. Deixa-lo entrar inflaria a populacao com uma operacao que a tabela
    # de inventario nao tem. Fica de fora da contagem, e o valor dele fica no JSON.
    conta = {k: v for k, v in pz.items() if k != 'si' and k in tab16}
    natab = {k: v for k, v in conta.items() if k in tab16}
    PAL = {5: 'Five', 6: 'Six', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve',
           13: 'thirteen', 14: 'fourteen', 15: 'fifteen', 16: 'sixteen',
           'T10': 'Ten', 'T9': 'Nine'}
    # ⚠️ as macros de «quantas passam» saem capitalizadas porque abrem frase. O PAL
    # antigo resolvia isso com chaves duplicadas por valor, o que quebra assim que a
    # contagem muda; agora a capitalizacao e explicita.
    def _pal(x, capitalizado=False):
        w = PAL[x]
        return w.capitalize() if capitalizado else w.lower()

    media = sr['REGRA_DA_FONTE_media_dos_cinco']
    assert abs(media - ke['media_crua_do_srinivas']) < 0.05, '⛔ as duas fontes discordam da media'
    nb = ke['naive_bayes_fora_do_segmento']
    sd = sr['ADAPTACAO_NOSSA_peso_sd_nos_cinco']
    peso0 = sr['pesos_da_adaptacao']['ke_edge_distribution']
    NUM = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 14: 'fourteen',
           15: 'fifteen', 16: 'sixteen'}

    def n(x):
        return f'{x:.1f}'

    L = [f'\\newcommand{{\\regraMedia}}{{{n(media)}}}',
         f'\\newcommand{{\\regraKe}}{{{n(nb)}}}',
         f'\\newcommand{{\\regraSrinivasAdapt}}{{{n(sd)}}}',
         f'\\newcommand{{\\regraKeQueda}}{{{abs(nb - media):.1f}}}',
         f'\\newcommand{{\\regraSrinivasAdaptQueda}}{{{abs(sd - media):.1f}}}',
         f'\\newcommand{{\\regraPesoZero}}{{{peso0:.5f}}}'.replace('{0.000', '{.000'),
         f'\\newcommand{{\\regraPesoMedia}}{{{1/5:.2f}}}'.replace('{0.', '{.'),
         f'\\newcommand{{\\qaroushFora}}{{{NUM[qa["fora_do_objetivo_de_qualidade"]]}}}',
         f'\\newcommand{{\\qaroushDe}}{{{NUM[qa["de"]]}}}',
         f'\\newcommand{{\\ctNiveis}}{{{ct["n_niveis"]}}}',
         f'\\newcommand{{\\autVerificadas}}{{{NUM[au["verificadas"]]}}}',
         f'\\newcommand{{\\autAutonomas}}{{{NUM[au["autonomas"]]}}}',
         f'\\newcommand{{\\autResto}}{{{NUM[au["verificadas"] - au["autonomas"]]}}}',
         f'\\newcommand{{\\vaModulo}}{{{va["modulo"]["VAScore_soma_crua_Eq20"]["media_sem_alinhados"]:.1f}}}',
         f'\\newcommand{{\\vaMelhorMembro}}{{{max(m["media_sem_alinhados"] for m in va["membros"].values()):.1f}}}',
         f'\\newcommand{{\\vaQueda}}{{{abs(va["modulo_menos_melhor_membro"]):.1f}}}',
         f'\\newcommand{{\\vaRuido}}{{{va["modulo"]["VAScore_soma_crua_Eq20"]["por_tipo"]["noise"]:.0f}}}',
         f'\\newcommand{{\\vaJpeg}}{{{va["modulo"]["VAScore_soma_crua_Eq20"]["por_tipo"]["jpeg"]:.0f}}}',
         f'\\newcommand{{\\pisoPop}}{{{_pal(len(conta))}}}',
         f'\\newcommand{{\\pisoPassam}}{{{_pal(sum(1 for v in conta.values() if v["passa"]), True)}}}',
         f'\\newcommand{{\\pisoTabPop}}{{{_pal(len(natab))}}}',
         f'\\newcommand{{\\pisoTabPassam}}{{{_pal(sum(1 for v in natab.values() if v["passa"]), True)}}}',
         f'\\newcommand{{\\pisoMenorLo}}'
         + '{$' + f'{min(v["ic_inferior"] for v in natab.values() if v["passa"]):+.3f}'
          + '$}',
         f'\\newcommand{{\\vaContraste}}{{{abs(ct2["qaroush"]["ponto"]):.1f}}}',
         f'\\newcommand{{\\vaIC}}{{[{sem_zero_negativo(ct2["qaroush"]["ic95"][1]):.1f},\\,{sem_zero_negativo(ct2["qaroush"]["ic95"][0]):.1f}]}}',
         f'\\newcommand{{\\koContraste}}{{{abs(ct2["korolkov"]["ponto"]):.1f}}}',
         f'\\newcommand{{\\koIC}}{{[{sem_zero_negativo(ct2["korolkov"]["ic95"][1]):.1f},\\,{sem_zero_negativo(ct2["korolkov"]["ic95"][0]):.1f}]}}',
         f'\\newcommand{{\\dupPares}}{{{du["sem_duplicatas"]["n_pares"]}}}',
         f'\\newcommand{{\\dupMediana}}{{{du["sem_duplicatas"]["mediana"]:.1f}}}',
         f'\\newcommand{{\\dupAbaixo}}{{{du["sem_duplicatas"]["abaixo_do_acaso"]}}}',
         # ⛔ BURACO MEDIDO EM 08/09: o piso de acaso 47,0 estava DIGITADO na prosa, e
         # trocar por 41,0 passava por todas as 23 guardas. Agora vem do arquivo.
         f'\\newcommand{{\\dupPiso}}{{{du["piso_do_acaso_pct"]:.1f}}}',
         # o mesmo piso na forma decimal que o metodo usa, para os dois nao poderem divergir
         f'\\newcommand{{\\dupPisoDec}}{{{sem_zero("%.3f" % (du["piso_do_acaso_pct"] / 100))}}}',
         f'\\newcommand{{\\dupComPares}}{{{du["com_duplicatas"]["n_pares"]}}}',
         f'\\newcommand{{\\dupComAbaixo}}{{{du["com_duplicatas"]["abaixo_do_acaso"]}}}',
         f'\\newcommand{{\\dupComMediana}}{{{du["com_duplicatas"]["mediana"]:.1f}}}',
         f'\\newcommand{{\\koModulo}}{{{ko["modulo_media"]:.1f}}}',
         f'\\newcommand{{\\koMelhorMembro}}{{{max(m["media"] for m in ko["membros"].values()):.1f}}}',
         f'\\newcommand{{\\koQueda}}{{{abs(ko["modulo_menos_melhor_membro"]):.1f}}}',
         f'\\newcommand{{\\koN}}{{{ko["n_segmentos"]}}}',
         f'\\newcommand{{\\koDe}}{{{ko["de_segmentos"]}}}',
         f'\\newcommand{{\\koPortao}}{{{ko["portao_laplacian_maior_dif"]:.1f}}}',
         f'\\newcommand{{\\vaCT}}{{{va["membros"]["qaroush_ct"]["media_sem_alinhados"]:.1f}}}',
         # ⛔ a formula antiga contava «com fonte E nao autonoma» = 14, que NAO e o numero de
         # trechos conferidos. A frase do corpo fala de EXCERTO, entao o campo e este.
         f'\\newcommand{{\\autTrechos}}{{{POREXT[au["trechos_conferidos"]]}}}',
         # ⛔ estas TRES vinham escritas a mao no .tex e sumiam a cada regeneracao.
         # A leitura dos PDFs das fontes mora em `o_que_cada_fonte_valida.json`.
         # ⛔ a sintese tem de citar a MESMA media que a tabela imprime: a das oito.
         # A de 74,3 exclui o tipo alinhado e vive na analise de sensibilidade.
         f'\\newcommand{{\\vaModuloOito}}{{{sum(va["modulo"]["VAScore_soma_crua_Eq20"]["por_tipo"].values())/8:.1f}}}',
         # ⛔ os quatro numeros da regra externa, da fonte e nao digitados na conclusao.
         # `si` fica FORA dos maximos: ele nao declara direcao e nao carrega veredito.
         f'\\newcommand{{\\pisoMelhorSens}}{{{sem_zero("%.3f" % max(v["sensibilidade_media"] for k, v in q15.items() if k != "si"))}}}',
         f'\\newcommand{{\\pisoMelhorGen}}{{{sem_zero("%.3f" % max(v["menor_rho_em_base_nao_vista"] for k, v in q15.items() if k != "si"))}}}',
         f'\\newcommand{{\\pisoLimSens}}{{{sem_zero("%.2f" % regra["sensibilidade_media_min"])}}}',
         f'\\newcommand{{\\pisoLimGen}}{{{sem_zero("%.2f" % regra["generalizacao_min"])}}}',
         f'\\newcommand{{\\valComPdf}}{{{POREXT[val["n_com_pdf"]]}}}',
         f'\\newcommand{{\\valPropriedade}}{{{POREXT[len(val["validam_a_propriedade_que_nomeiam"])]}}}',
         f'\\newcommand{{\\valSoResumo}}{{{POREXT[len(val["avaliam_so_o_resumo"])]}}}',
         # ⛔ 22/09 (parecer v2): a prosa somava 2 + 7 = 9 de DEZ fontes lidas. A decima e
         # o Korolkov, que nao testa nem a regra nem os pesos; sem esta macro a categoria
         # desaparecia da contagem e o leitor ficava com um trabalho sem classificacao.
         f'\\newcommand{{\\valSemTeste}}{{{POREXT[val["n_com_pdf"] - len(val["validam_a_propriedade_que_nomeiam"]) - len(val["avaliam_so_o_resumo"])]}}}',
         # ⛔ a contagem das fontes vinha digitada em cinco lugares do corpo. Ela e
         # medida: 16 = as 15 da literatura de sumarizacao + o `si`, que vem da ITU-T.
         f'\\newcommand{{\\fontesOperacoes}}{{{POREXT[prov["n_operacoes_da_triagem"]]}}}',
         f'\\newcommand{{\\fontesDaLiteratura}}{{{POREXT[prov["n_operacoes_das_15"]]}}}',
         f'\\newcommand{{\\fontesDaLiteraturaN}}{{{prov["n_operacoes_das_15"]}}}',
         f'\\newcommand{{\\fontesTrabalhos}}{{{POREXT[prov["n_trabalhos_das_15"]]}}}',
         # ⛔ a concordancia que SOBRA depois da substituicao, contra o acaso dos 42
         # clusters. Sem isto o «muda 22 de 42» deixa em aberto o que os outros 20 sao.
         f'\\newcommand{{\\subResta}}{{{sub["por_linha"]["liqe_x_implantada"]["acertos"]}}}',
         f'\\newcommand{{\\subPct}}{{{sub["por_linha"]["liqe_x_implantada"]["pct"]:.1f}}}',
         f'\\newcommand{{\\subAcaso}}{{{100 * sub["acaso_medio"]:.1f}}}',
         f'\\newcommand{{\\subKappa}}{{{sem_zero("%.3f" % sub["por_linha"]["liqe_x_implantada"]["kappa_contra_o_acaso"])}}}',
         f'\\newcommand{{\\subIC}}{{[{sub["por_linha"]["liqe_x_implantada"]["ic_bloco_de_topico"][0]:.1f}, '
         f'{sub["por_linha"]["liqe_x_implantada"]["ic_bloco_de_topico"][1]:.1f}]}}',
         # ⛔ «inverte em pelo menos um tipo» e quase certo por acaso. O que separa e que
         # TODA celula abaixo do acaso e significativa, e a moeda de controle nao acumula.
         f'\\newcommand{{\\invCelulas}}{{{sum(len(v["tipos_abaixo_de_50"]) for v in inv["por_operacao"].values())}}}',
         f'\\newcommand{{\\invTestes}}{{{inv["n_testes"]}}}',
         # ⛔ CORRIGIDO em 09/09: o binomial tratava os 100 pares como independentes, e eles
         # sao 20 SEGMENTOS x 5 niveis. Na unidade declarada (troca de sinal por segmento,
         # nula exata) sobrevivem 22 das 35, em 14 das 15 operacoes, e nao 35 em 15.
         f'\\newcommand{{\\invSig}}{{{blo["significativas_sob_o_bloco_de_segmento"]}}}',
         f'\\newcommand{{\\invOpsSig}}{{{POREXT[blo["operacoes_com_ao_menos_uma_significativa_no_bloco"]]}}}',
         # ⛔ O DEGRAU SEGUINTE, 21/09: o parecer externo (M43/M44/E22) apontou que os 20
         # segmentos vem de 13 TOPICOS e que o teste por celula ignorava essa camada,
         # enquanto o bootstrap da manchete ja a respeitava. ⭐ E ao montar o mapa apareceu
         # que `cessar_fogo_ucrania` e `ucrania` sao O MESMO MATERIAL (mesmos tres .mp4; os
         # dois segmentos do `ucrania_band.mp4` se sobrepoem, [42,10; 69,18] dentro de
         # [41,44; 86,54]), entao o bloco principal funde os dois: 12, e nao 13.
         # ⭐ O que NAO depende da unidade: as cinco celulas de 0 de 100 sobrevivem nas tres.
         f'\\newcommand{{\\invSigTop}}{{{top["significativas_sob_o_bloco_de_topico_12"]}}}',
         f'\\newcommand{{\\invOpsSigTop}}{{{POREXT[top["operacoes_com_significativa_no_topico_12"]]}}}',
         f'\\newcommand{{\\invBlocos}}{{{POREXT[top["n_blocos_principal"]]}}}',
         f'\\newcommand{{\\invBlocosN}}{{{top["n_blocos_principal"]}}}',
         f'\\newcommand{{\\invRotulos}}{{{POREXT[top["n_rotulos_de_topico"]]}}}',
         f'\\newcommand{{\\invSigRotulo}}{{{top["significativas_sob_o_rotulo_de_topico_13"]}}}',
         f'\\newcommand{{\\invPerfeitas}}{{{POREXT[top["celulas_perfeitas_0_de_100"]]}}}',
         # ⛔ 22/09 (parecer v2, criterio 42): a LATERALIDADE nao estava declarada, e o
         # resultado depende dela. Com 12 blocos o menor p unilateral e 2^-12 = 2,44e-4 e
         # o primeiro corte de Holm e 0,05/120 = 4,17e-4: o unilateral passa, um bilateral
         # simetrico NAO passaria celula nenhuma. Sai por macro para nao ser digitado.
         f'\\newcommand{{\\invPmin}}{{{sci(top["lateralidade"]["menor_p_possivel"])}}}',
         f'\\newcommand{{\\invCorteHolm}}{{{sci(top["lateralidade"]["primeiro_corte_de_holm"])}}}',
         # ⛔ 22/09 (parecer v2, V2-062): a reescrita apagou POR QUE 74,3 e 77,5 sao
         # numeros diferentes do mesmo modulo. Nao sao inconsistencia: o contraste com o
         # melhor componente exclui o tipo alinhado a construcao do modulo (satur no
         # Qaroush, dark no Korolkov), e a Tabela 6 reporta a media dos OITO tipos.
         # ⭐ Populacao e exclusao saem por macro para nao voltarem a sumir num corte.
         f'\\newcommand{{\\vaTipoFora}}{{{va["tipos_fora"][0]}}}',
         f'\\newcommand{{\\vaPares}}{{{7 * 5 * 20}}}',
         f'\\newcommand{{\\vaMediaOito}}{{{sum(va["modulo"]["VAScore_soma_crua_Eq20"]["por_tipo"].values()) / 8:.1f}}}',
         f'\\newcommand{{\\koTipoFora}}{{{ko["tipos_fora"][0]}}}',
         f'\\newcommand{{\\koPares}}{{{7 * 5 * ko["n_segmentos"]}}}',
         f'\\newcommand{{\\koParesOito}}{{{8 * 5 * ko["n_segmentos"]}}}',
         f'\\newcommand{{\\koMediaOito}}{{{sum(ko["modulo_por_tipo"].values()) / 8:.1f}}}',
         # ⭐ a energia por tipo: quantos tipos ADICIONAM energia, e as razoes extremas
         f'\\newcommand{{\\eneAdicionam}}{{{POREXT[sum(1 for v in ene.values() if v["adiciona_energia"])]}}}',
         f'\\newcommand{{\\eneRuido}}{{{ene["noise"]["razao_mediana_ao_original"]:.1f}}}',
         f'\\newcommand{{\\eneMaiorSemRuido}}{{{max(v["razao_mediana_ao_original"] for k, v in ene.items() if k != "noise"):.2f}}}',
         f'\\newcommand{{\\eneJpeg}}{{{ene["jpeg"]["razao_mediana_ao_original"]:.2f}}}',
         f'\\newcommand{{\\invMoeda}}{{{"none" if inv["controle_da_moeda"]["quantas_acumulam_significancia"] == 0 else POREXT[inv["controle_da_moeda"]["quantas_acumulam_significancia"]]}}}',
         # ⭐ o mesmo teste na outra familia: sem ele a leitura e de um lado so
         f'\\newcommand{{\\invModelosLimpos}}{{{POREXT[inv["a_outra_familia"]["sem_nenhum_tipo_abaixo"]]}}}',
         # ⭐ 22/09 (parecer v4, 2.2): o corpo usa acuracia ESTRITA (empate no denominador)
         #    e a S27 usa a DECISIVA (empate fora). As duas convivem e as legendas nao
         #    diziam qual era qual. Estas macros deixam a diferenca dimensionada: so
         #    quatro operacoes empatam, e nas outras onze as duas acuracias coincidem.
         f'\\newcommand{{\\empOps}}{{{POREXT[sum(1 for v in inv["empates_por_operacao"].values() if v)]}}}',
         f'\\newcommand{{\\empSemOps}}{{{POREXT[sum(1 for v in inv["empates_por_operacao"].values() if not v)]}}}',
         f'\\newcommand{{\\empMaior}}{{{max(inv["empates_por_operacao"].values())}}}',
         # ⭐ 22/09 (parecer v4, 2.4): a fusao dos dois rotulos que partilham os tres .mp4
         #    era feita nos pares (12 blocos) e NAO na aplicacao (19 topicos). Medida:
         #    18 blocos, e o veredito nao muda. O reconstrutor do vetor por cluster e
         #    validado contra o IC publicado antes de qualquer conta.
         f'\\newcommand{{\\fusBlocos}}{{{fus["por_linha"]["liqe_x_implantada"]["fundido"]["n_blocos"]}}}',
         f'\\newcommand{{\\fusIC}}{{[{fus["por_linha"]["liqe_x_implantada"]["fundido"]["ic"][0]:.1f}, '
         f'{fus["por_linha"]["liqe_x_implantada"]["fundido"]["ic"][1]:.1f}]}}',
         # ⭐ 22/09 (parecer v5, 2.1): a MESMA fusao aplicada a concordancia que decide a
         #    elegibilidade, reusando a inferencia publicada atras de flag. O controle
         #    (sem a flag reproduzir o publicado) roda antes e esta no JSON.
         f'\\newcommand{{\\finLiqe}}{{{ic(fin["por_analise"]["concordancia_no_dominio_liqe"]["ic_18"])}}}',
         f'\\newcommand{{\\finSift}}{{{ic(fin["por_analise"]["concordancia_no_dominio_implantada"]["ic_18"])}}}',
         # ⭐ os dois contrastes DOVER-T sob a mesma fusao, para a 4.6
         f'\\newcommand{{\\finDovComp}}{{[{fin["por_analise"]["dover_t_substituicao_completa"]["ic_18"][0]:+.1f}, '
         f'{fin["por_analise"]["dover_t_substituicao_completa"]["ic_18"][1]:+.1f}]}}',
         f'\\newcommand{{\\finDovCas}}{{[{fin["por_analise"]["dover_t_entradas_casadas"]["ic_18"][0]:.1f}, '
         f'{fin["por_analise"]["dover_t_entradas_casadas"]["ic_18"][1]:.1f}]}}',
         # ⭐ 23/09 (parecer v8, 2.2): os MESMOS quatro sob os 19 ROTULOS SEPARADOS, que
         #    o suplementar ja imprimia digitados e sem rotulo. Saem do mesmo arquivo e do
         #    mesmo dicionario que os `fin*`, so que do campo `ic_19`: assim os dois
         #    conjuntos nunca podem divergir de fonte, e o par (principal, sensibilidade)
         #    e legivel no codigo.
         f'\\newcommand{{\\senBlocos}}{{{fus["por_linha"]["liqe_x_implantada"]["sem_fundir"]["n_blocos"]}}}',
         f'\\newcommand{{\\senLiqe}}{{{ic(fin["por_analise"]["concordancia_no_dominio_liqe"]["ic_19"])}}}',
         f'\\newcommand{{\\senSift}}{{{ic(fin["por_analise"]["concordancia_no_dominio_implantada"]["ic_19"])}}}',
         f'\\newcommand{{\\senDovComp}}{{[{fin["por_analise"]["dover_t_substituicao_completa"]["ic_19"][0]:+.1f}, '
         f'{fin["por_analise"]["dover_t_substituicao_completa"]["ic_19"][1]:+.1f}]}}',
         f'\\newcommand{{\\senDovCas}}{{[{fin["por_analise"]["dover_t_entradas_casadas"]["ic_19"][0]:.1f}, '
         f'{fin["por_analise"]["dover_t_entradas_casadas"]["ic_19"][1]:.1f}]}}',
         # ⭐ 25/09: a REDUCAO. Trocar o escore pela contagem de descritores nao muda
         #    escolha nenhuma; trocar pelo numero de quadros retidos muda quase metade.
         f'\\newcommand{{\\redEscolhas}}{{{_red["⭐_por_quantidade_substituta"]["n_desc"]["escolhas_iguais"]}}}',
         f'\\newcommand{{\\redDe}}{{{_red["⭐_por_quantidade_substituta"]["n_desc"]["de_clusters"]}}}',
         f'\\newcommand{{\\redQuadros}}{{{_red["⭐_por_quantidade_substituta"]["n_frames"]["escolhas_iguais"]}}}',
         f'\\newcommand{{\\redRhoQuadros}}{{{sem_zero("%+.3f" % _red["correlacao_com_o_score_publicado"]["n_frames"]["spearman_com_bovw_sum"])}}}',
         f'\\newcommand{{\\redRhoDens}}{{{sem_zero("%+.3f" % _red["correlacao_com_o_score_publicado"]["kp_density"]["spearman_com_bovw_sum"])}}}',
         # ⚠️ 27/09 (parecer): por EXTENSO. A frase da 4.5 diz «for 12 of the
         # fifteen operations ... the remaining 3», e o `\\fontesDaLiteratura`
         # do meio ja sai por extenso: numeral e palavra na mesma enumeracao.
         f'\\newcommand{{\\basePiorKadid}}{{{POREXT[_bp["KADID"]]}}}',
         f'\\newcommand{{\\basePiorKoniq}}{{{POREXT[_bp["KonIQ"]]}}}',
         # ⭐ 22/09 (M12): o descritor excluido tem NOME e a condicao e verificavel.
         f'\\newcommand{{\\surfOpenCV}}{{{srf["opencv"]}}}',
         # ⭐ 22/09 (parecer v7, 2.4): a populacao dos dezessete. Sao as quinze do
         #    inventario direcional mais duas que a regra de quadro isolado exclui.
         f'\\newcommand{{\\dezExtraUm}}{{Sobel variation coefficient}}',
         f'\\newcommand{{\\dezExtraDois}}{{Qaroush motion}}',
         f'\\newcommand{{\\invModelos}}{{{POREXT[inv["a_outra_familia"]["n_modelos"]]}}}',
         # ⛔ BURACO MEDIDO EM 08/09: os tres numeros da manchete estavam DIGITADOS, e
         # trocar o +34,4 por +31,4 passava por todas as guardas. Agora vem do arquivo,
         # e o IC ao lado ja vem do mesmo lugar pela guarda de unidade.
         f'\\newcommand{{\\mchImplantada}}{{{mch["implantada"]:.1f}}}',
         f'\\newcommand{{\\mchLiqe}}{{{mch["liqe"]:.1f}}}',
         f'\\newcommand{{\\mchDif}}{{{mch["dif"]:.1f}}}',
         f'\\newcommand{{\\casQuadrosMedia}}{{{r3s["mean_common_frames"]:.2f}}}',
         # ⛔ os dois ICs vinham digitados (ou faltavam) no corpo. `as_tres_unidades`
         #    ja trazia segmento, topico e par; o parecer pediu o de topico ao lado.
         f'\\newcommand{{\\mchICSeg}}{{[{mch["as_tres_unidades"]["bloco_de_segmento"]["imprime"][0]}, '
         f'{mch["as_tres_unidades"]["bloco_de_segmento"]["imprime"][1]}]}}',
         f'\\newcommand{{\\mchICTop}}{{[{mch["as_tres_unidades"]["bloco_de_topico"]["imprime"][0]}, '
         f'{mch["as_tres_unidades"]["bloco_de_topico"]["imprime"][1]}]}}',
         f'\\newcommand{{\\mchTopicos}}{{{mch["as_tres_unidades"]["bloco_de_topico"]["n_blocos"]}}}',
         # ⭐ 22/09 (parecer v2): o corpo reconhece que dois rotulos de topico sao o mesmo
         #    material e precisam ser fundidos, e o IC ao lado vinha reamostrado pelos 13
         #    rotulos. Agora o principal e o FUNDIDO, e o sem fundir sai ao lado para que
         #    a escolha seja verificavel na pagina em vez de declarada.
         f'\\newcommand{{\\mchICTopSem}}{{[{mch["as_tres_unidades"]["bloco_de_rotulo_13_sem_fundir"]["imprime"][0]}, '
         f'{mch["as_tres_unidades"]["bloco_de_rotulo_13_sem_fundir"]["imprime"][1]}]}}',
         # e o numero de computacoes distintas sai dos pares, e nao digitado:
         # n(n-1)/2 = 55 pares implica onze operacoes distintas
         f'\\newcommand{{\\dupDistintas}}{{{POREXT[int((1 + (1 + 8 * du["sem_duplicatas"]["n_pares"]) ** .5) / 2)]}}}',
         # ⭐ as tres excecoes do mecanismo: um revisor pergunta o que sao, e a resposta
         # muda o estatuto da fatoracao. Sao empates de margem, e isso esta medido.
         f'\\newcommand{{\\excDelta}}{{{POREXT[exc["maior_delta_de_contagem_entre_as_discordancias"]]}}}',
         f'\\newcommand{{\\excMediana}}{{{exc["n_desc_medida"]["mediana"]:,.0f}}}'.replace(',', '{,}'),
         # ⛔ o bloco DOVER seguia com decimal digitado, e a mutacao mostrou que trocar
         # +25,5 por +22,5 passava. Os tres vem da tabela 4, que ja reproduz da fonte.
         f'\\newcommand{{\\dovImplantada}}{{{tab4["SIFT+BoVW"]["fonte_DOVER_T"]:.1f}}}',
         f'\\newcommand{{\\dovLiqe}}{{{tab4["LIQE"]["fonte_DOVER_T"]:.1f}}}',
         f'\\newcommand{{\\dovDif}}{{{tab4["LIQE"]["fonte_DOVER_T"] - tab4["SIFT+BoVW"]["fonte_DOVER_T"]:.1f}}}',
         # e a anticorrelacao por construcao do CT, que e uma afirmacao forte sobre a
         # equacao de outra pessoa: sai do arquivo, nao da minha mao.
         f'\\newcommand{{\\ctRho}}{{{ct["spearman_com_o_contraste_real"]["a_Eq8_com_modulo"]:.4f}}}',
         # ⛔ o resto do bloco DOVER, que a mutacao mediu como solto. Todos vem dos dois
         # arquivos de reanalise, e nao mais da minha mao.
         f'\\newcommand{{\\dovICTopico}}{{[{tec["global_achievable_range_percent"]["topic_block_ci95"][0]:+.1f},{tec["global_achievable_range_percent"]["topic_block_ci95"][1]:+.1f}]}}',
         f'\\newcommand{{\\dovICHier}}{{[{tec["global_achievable_range_percent"]["hierarchical_ci95"][0]:+.1f},{tec["global_achievable_range_percent"]["hierarchical_ci95"][1]:+.1f}]}}',
         f'\\newcommand{{\\dovCru}}{{{sem_zero("%+.4f" % tec["raw_mean"]["estimate"])}}}',
         f'\\newcommand{{\\dovCruTopico}}{{[{sem_zero("%+.4f" % tec["raw_mean"]["topic_block_ci95"][0])},{sem_zero("%+.4f" % tec["raw_mean"]["topic_block_ci95"][1])}]}}',
         f'\\newcommand{{\\dovCruHier}}{{[{sem_zero("%+.4f" % tec["raw_mean"]["hierarchical_ci95"][0])},{sem_zero("%+.4f" % tec["raw_mean"]["hierarchical_ci95"][1])}]}}',
         f'\\newcommand{{\\dovPosicao}}{{{tec["mean_cluster_position_percent"]["estimate"]:.1f}}}',
         f'\\newcommand{{\\dovCortaDez}}{{{r2["technical"]["range_sensitivity"]["exclude_bottom_10pct"]["global_achievable_range_difference"]:+.1f}}}',
         f'\\newcommand{{\\dovCortaVinteCinco}}{{{r2["technical"]["range_sensitivity"]["exclude_bottom_25pct"]["global_achievable_range_difference"]:+.1f}}}',
         f'\\newcommand{{\\dovSoma}}{{{r2["overall"]["liqe_minus_sift"]["global_achievable_range_percent"]["estimate"]:+.1f}}}',
         f'\\newcommand{{\\dovCasado}}{{{cas["global_achievable_range_percent"]["estimate"]:+.1f}}}',
         f'\\newcommand{{\\dovCasadoTopico}}{{[{cas["global_achievable_range_percent"]["topic_block_ci95"][0]:.1f},{cas["global_achievable_range_percent"]["topic_block_ci95"][1]:.1f}]}}',
         f'\\newcommand{{\\dovCasadoHier}}{{[{cas["global_achievable_range_percent"]["hierarchical_ci95"][0]:.1f},{cas["global_achievable_range_percent"]["hierarchical_ci95"][1]:.1f}]}}',
         f'\\newcommand{{\\dovCasadoCru}}{{{sem_zero("%+.4f" % cas["raw_mean"]["estimate"])}}}',
         f'\\newcommand{{\\dovMaximo}}{{{tec["selected_maximum_percent"]["estimate"]:.1f}}}',
         # ⭐ e o ultimo decimal digitado da prosa. Ancorar mostrou que ele e o TETO:
         # nos 42 clusters as quatorze escolhem todos os membros.
         f'\\newcommand{{\\escMedia}}{{{esc["como_impressa"]:.2f}}}',
         f'\\newcommand{{\\escGrandes}}{{{POREXT[esc["clusters_com_mais_de_dois_membros"]]}}}',
         # ⭐ as quinze nao sao quinze medidas distintas, e isso e um fato sobre a
         # LITERATURA: ela reusa as mesmas estatisticas com nomes diferentes.
         f'\\newcommand{{\\effPosto}}{{{POREXT[eff["posto_dos_escores_crus"]]}}}',
         f'\\newcommand{{\\effMeff}}{{{eff["M_eff_li_ji_spearman"]:.0f}}}',
         # ⭐ o veredito da porta e fragil? Medido: nenhuma das quinze vira em 10^4
         # reamostragens das referencias, e nenhum intervalo encosta na barra.
         f'\\newcommand{{\\refViram}}{{{"none" if ref["⭐_VIRAM_EM_ALGUMA_REAMOSTRA"]["n"] == 0 else POREXT[ref["⭐_VIRAM_EM_ALGUMA_REAMOSTRA"]["n"]]}}}',
         f'\\newcommand{{\\refTocam}}{{{"none" if ref["⭐_IC_TOCA_A_BARRA"]["n"] == 0 else POREXT[ref["⭐_IC_TOCA_A_BARRA"]["n"]]}}}',
         f'\\newcommand{{\\refB}}{{{ref["B"]:,}}}'.replace(',', '{,}'),
         # ⛔ a discussao inferia «as escolhas internas contribuem» da diferenca entre 22 e
         # 16, e o McNemar pareado nos mesmos 42 clusters NAO resolve essa diferenca
         # (p 0,146). A evidencia direta e o terceiro contraste, que o artigo nao reportava:
         # mantido o scorer e trocados so o quadro comum e o pooling, 12 decisoes ja mudam.
         f'\\newcommand{{\\casSoCasamento}}{{{cas3["contagens"]["so_o_casamento_scorer_fixo_12"]}}}',
         f'\\newcommand{{\\casCompleta}}{{{cas3["contagens"]["operacao_completa_22"]}}}',
         f'\\newcommand{{\\casP}}{{{sem_zero("%.3f" % cas3["McNemar_pareado_nos_mesmos_42"]["operacao_completa (22) vs so_o_casamento (12)"]["p_mcnemar_exato"])}}}',
         # ⭐ 12/09: o McNemar trata os 42 clusters como independentes e eles vem de 19
         # topicos. O mesmo contraste pela troca de sinal EM BLOCO, que e o mecanismo que
         # o artigo ja usa nos 800 pares, enumerada exatamente sobre os topicos que
         # carregam discordante.
         f'\\newcommand{{\\mcnBloco}}{{{sem_zero("%.3f" % mcb["COM_O_TOPICO_COMO_UNIDADE"]["p_troca_de_sinal_em_bloco"])}}}',
         f'\\newcommand{{\\mcnBlocos}}{{{mcb["COM_O_TOPICO_COMO_UNIDADE"]["topicos_que_carregam_discordante"]}}}',
         f'\\newcommand{{\\mcnAtrib}}{{{mcb["COM_O_TOPICO_COMO_UNIDADE"]["atribuicoes_enumeradas"]}}}',
         f'\\newcommand{{\\mcnSemMaior}}{{{sem_zero("%.3f" % mcb["DEPENDE_DE_UM_TOPICO_SO"]["p_sem_esse_topico"])}}}',
         # ⭐ o protocolo de identificacao: acervo, instrumento de busca MEDIDO, criterio
         # de triagem e cobertura declarada. Tudo do disco; nada digitado.
         f'\\newcommand{{\\acvPdfs}}{{{acv["n_pdfs"]}}}',
         f'\\newcommand{{\\acvSemDedicado}}{{{acv["n_sem_nriqa_dedicado"]}}}',
         f'\\newcommand{{\\acvUsamOperacao}}{{{acv["dos_sem_dedicado_quantos_usam_operacao"]}}}',
         f'\\newcommand{{\\acvTermos}}{{{POREXT[len(acc["ANTES"]["por_termo"])]}}}',
         f'\\newcommand{{\\varrN}}{{{vrr["n_artigos"]}}}',
         f'\\newcommand{{\\varrPrec}}{{{sem_zero("%.2f" % vrr["DEPOIS"]["precisao"])}}}',
         f'\\newcommand{{\\varrCob}}{{{sem_zero("%.2f" % vrr["DEPOIS"]["cobertura"])}}}',
         f'\\newcommand{{\\triMapa}}{{{cob["⭐_A_TRIAGEM_TEM_CRITERIO"]["no_mapa"]}}}',
         f'\\newcommand{{\\triTriadas}}{{{cob["⭐_A_TRIAGEM_TEM_CRITERIO"]["triadas"]}}}',
         f'\\newcommand{{\\triForaComDirecao}}{{{POREXT[len(cob["⭐_A_TRIAGEM_TEM_CRITERIO"]["com_direcao_mas_fora_da_triagem"])]}}}',
         f'\\newcommand{{\\cobMencoes}}{{{cob["COBERTURA_DAS_15"]["mencoes_cobertas"]}}}',
         f'\\newcommand{{\\cobTotal}}{{{cob["mencoes_totais"]}}}',
         f'\\newcommand{{\\cobFora}}{{{cob["COBERTURA_DAS_15"]["mencoes_fora"]}}}',
         f'\\newcommand{{\\cobNaoTriavel}}{{{cob["COBERTURA_DAS_15"]["nao_triaveis_por_fonte_subespecificada"]}}}',
         f'\\newcommand{{\\cobSemDirecao}}{{{cob["fora_da_triagem"]["por_direcao_nao_declarada"]}}}',
         f'\\newcommand{{\\cobSemRegra}}{{{cob["fora_da_triagem"]["por_regra_de_combinacao_ausente"]}}}',
         # ⭐ o unico eixo em que as operacoes vao bem, com a fragilidade ao lado. As duas
         # familias entram pela MESMA regra: fora quem nao carrega veredito.
         f'\\newcommand{{\\pisoModN}}{{{POREXT[pd2["modelos"]["n"]]}}}',
         f'\\newcommand{{\\pisoKapOp}}{{{sem_zero("%.3f" % pd2["operacoes"]["kappa_mediano_de_todas"])}}}',
         f'\\newcommand{{\\pisoKapMod}}{{{sem_zero("%.3f" % pd2["modelos"]["kappa_mediano_de_todos"])}}}',
         f'\\newcommand{{\\pisoFrageis}}{{{POREXT[pd2["fragilidade_ao_tirar_um_topico"]["quantas_das_que_passam_viram"]]}}}',
         # ⭐ a manchete depende de quais tipos entraram? Os dois numeros, sem escolher um.
         f'\\newcommand{{\\tipoSemAlinhados}}{{{POREXT[mtip["sem os dois tipos alinhados"]["invertem"]]}}}',
         f'\\newcommand{{\\tipoSemRuido}}{{{POREXT[mtip["sem o ruido branco"]["invertem"]]}}}',
         # ⭐ a objecao «voces implementaram errado», respondida com numero
         f'\\newcommand{{\\reiMedia}}{{{rei["reimplementacao"]["media"]:.1f}}}',
         f'\\newcommand{{\\reiRuido}}{{{rei["reimplementacao"]["por_tipo"]["noise"]:.0f}}}',
         f'\\newcommand{{\\reiJpeg}}{{{rei["reimplementacao"]["por_tipo"]["jpeg"]:.0f}}}',
         f'\\newcommand{{\\reiSatur}}{{{rei["reimplementacao"]["por_tipo"]["satur"]:.0f}}}',
         f'\\newcommand{{\\reiPiorModelo}}{{{rei["pior_modelo_publicado"]:.1f}}}',
         # ⛔ o 797 aparecia DIGITADO nas quatro secoes. Uma macro, um arquivo.
         f'\\newcommand{{\\mecConcordam}}{{{int(str(par["pares_em_que_score_e_contagem_concordam"]).split()[0])}}}',
         # ⭐ a classe concorda mais com algo de FORA do que consigo mesma
         f'\\newcommand{{\\claPar}}{{{sem_zero("%.3f" % cla["kappa_par_a_par_entre_operacoes"]["mediana"])}}}',
         f'\\newcommand{{\\claRazao}}{{{cla["razao_das_medianas"]:.0f}}}',
         # ⭐ a ponte entre o caso implantado e a classe: ele e o meio dela
         f'\\newcommand{{\\tipAbaixo}}{{{POREXT[tip["classe_de_sumarizacao"]["quantas_ficam_abaixo_da_implantada"]]}}}',
         f'\\newcommand{{\\tipDe}}{{{POREXT[tip["classe_de_sumarizacao"]["n"]]}}}',
         f'\\newcommand{{\\tipMediana}}{{{tip["classe_de_sumarizacao"]["mediana"]:.1f}}}',
         # ⭐ o resumo agora alcanca macro: os numeros MEDIDOS dele saem daqui tambem
         f'\\newcommand{{\\resInverteRuido}}{{{100 - [l for l in json.load(open(QB / "TABELA_FINAL.json"))["linhas"] if l["nome"] == "SIFT+BoVW"][0]["acc"]["noise"]:.0f}}}',
         f'\\newcommand{{\\resZeroRuido}}{{{POREXT[sum(1 for v in inv["por_operacao"].values() if v["acuracia_por_tipo"].get("noise") == 0.0)]}}}',
         f'\\newcommand{{\\resElegiveis}}{{{POREXT[len(ele["elegiveis"])]}}}',
         f'\\newcommand{{\\resCombinacoes}}{{{POREXT[len(comb["por_combinacao"])]}}}',
         # o «treze das quinze sob ruido», que aparece no resumo, no intro e na 4.1
         # ⚠️ `is not None`, nunca `or`: acuracia 0,0 e falsy e sumiria da conta
         f'\\newcommand{{\\resRuido}}{{{POREXT[sum(1 for v in inv["por_operacao"].values() if (lambda a: a is not None and a < 50)(v["acuracia_por_tipo"].get("noise")))]}}}',
         # ⚠️ versao CAPITALIZADA, para quando o numero abre a frase: sem ela o resumo
         # saiu com «thirteen prefer...» em minuscula depois de ponto.
         f'\\newcommand{{\\resRuidoC}}{{{POREXT[sum(1 for v in inv["por_operacao"].values() if (lambda a: a is not None and a < 50)(v["acuracia_por_tipo"].get("noise")))].capitalize()}}}',
         f'\\newcommand{{\\resRuidoN}}{{{sum(1 for v in inv["por_operacao"].values() if (lambda a: a is not None and a < 50)(v["acuracia_por_tipo"].get("noise")))}}}',
         # ⭐ a razao entre os dois canais, para o graphical abstract nao digitar
         f'\\newcommand{{\\mecRazaoCanais}}{{{.938 / .098:.1f}}}',
         # ===================================================================
         # ⭐ O RESUMO GRAFICO. Cada numero da peca sai daqui; nenhum digitado
         # no .tex. Antes desta secao ela trazia onze numeros a mao, e nenhuma
         # guarda os conferia contra a fonte: foi assim que ela envelheceu
         # enquanto o artigo mudava.
         # ===================================================================
         # ⛔ quantas das 15 passam as DUAS condicoes externas. O
         # `as_15_na_regra_do_artigo.json` tem DEZESSEIS entradas, nao quinze:
         # a extra e o `si`, que vem da ITU-T e nao da literatura de
         # sumarizacao (`_por_que_16_e_nao_15` na proveniencia). Sem filtrar, a
         # peca imprimiria «0 de 16» com aparencia de certo -- e o numerador e
         # zero nos dois universos, que e o que tornaria o erro invisivel.
         f'\\newcommand{{\\triagemPassam}}{{{_tri_passam}}}',
         # os nomes dos tres, para o rodape nao digitar a lista
         f'\\newcommand{{\\resElegiveisNomes}}{{{_tri_nomes}}}',
         # ⭐ o desenho A, medido do proprio arquivo de pares: 20 segmentos x 8
         # tipos x 5 niveis. O «800» aparecia em tres lugares da peca a mao.
         f'\\newcommand{{\\parConstruidos}}{{{_pa_seg * _pa_tipos * _pa_niveis}}}',
         f'\\newcommand{{\\nTipos}}{{{_pa_tipos}}}',
         f'\\newcommand{{\\nBases}}{{{_tri_bases}}}',
         # ⭐ o painel 1 do resumo grafico como GRAFICO, nao como frase: quantas
         # das 15 invertem em cada um dos 8 tipos, em lista que o \\foreach do
         # TikZ le direto. Sem isto o painel dizia so «13/15» e perdia que o
         # ruido e um caso destacado, nao o comportamento geral.
         f'\\newcommand{{\\invPorTipoLista}}{{{_inv_lista}}}',
         # ⭐ o painel 4: a particao MEDIDA de 21 operacoes em 18 resumos e um
         # grupo de 3, um de 2 e dezesseis sozinhos. O desenho le os tamanhos
         # daqui; desenha-los a mao seria inventar a forma da particao.
         f'\\newcommand{{\\disGruposLista}}{{{_dis_grupos}}}',
         # ⚠️ versoes NUMERICAS: as macros de prosa saem por extenso («nineteen»,
         # «ten») e o \\foreach do TikZ nao desenha uma palavra. Mesma fonte,
         # para os dois nunca divergirem.
         f'\\newcommand{{\\resCombinacoesN}}{{{len(comb["por_combinacao"])}}}',
         f'\\newcommand{{\\invModelosN}}{{{_inv_mod_n}}}',
         f'\\newcommand{{\\resElegiveisN}}{{{len(ele["elegiveis"])}}}',
         # ⛔ quantas das 19 combinacoes passam as DUAS portas: zero. NAO usar
         # `quantas_combinacoes_passam`, que vale 1 -- esse campo conta quem
         # passa UMA porta (a media_z passa sensibilidade e cai na
         # generalizacao, com KonIQ .061 contra .65). O campo das duas portas
         # juntas e `ELEGIVEIS_PELAS_DUAS_PORTAS`, e e esse que sustenta o
         # «None of the nineteen» do corpo.
         f'\\newcommand{{\\triagemCombPassam}}'
         f'{{{comb["ELEGIVEIS_PELAS_DUAS_PORTAS"]["n_combinacoes"]}}}',
         # ⚠️ o subtitulo do resumo grafico e uma linha de numerais para
         # varredura rapida: sem esta versao ele saia «15 operations from
         # eleven source works», misturando algarismo e palavra na mesma frase.
         f'\\newcommand{{\\fontesTrabalhosN}}{{{prov["n_trabalhos_das_15"]}}}',
         # ⛔ 27/09 (parecer, D): este numero estava DIGITADO no corpo como
         # «+.994» enquanto a Tabela S33 imprimia «+.995». Nao eram duas
         # medicoes: e o mesmo 0,9945, arredondado por dois caminhos. Agora sai
         # daqui com o MESMO formato do gerador da S33, entao os dois nao podem
         # mais divergir.
         f'\\newcommand{{\\mecRhoContagem}}'
         f'{{{("%+.3f" % _red_rho).replace("0.", ".")}}}',
         # ⛔ 27/09 (parecer, B): a frase do piso no dominio trazia CINCO numeros
         # digitados a mao (32, 42, .551, 21, 1.3, .056). Saem todos daqui, do
         # arquivo que ja os reproduzia por bootstrap.
         f'\\newcommand{{\\pisoDe}}{{{_piso["MODELO liqe"]["de"]}}}',
         f'\\newcommand{{\\pisoLiqeAcertos}}{{{_piso["MODELO liqe"]["acertos"]}}}',
         f'\\newcommand{{\\pisoLiqeKappa}}'
         f'{{{sem_zero("%.3f" % _piso["MODELO liqe"]["kappa_uniform"])}}}',
         f'\\newcommand{{\\pisoSiftAcertos}}{{{_piso_op["acertos"]}}}',
         f'\\newcommand{{\\pisoSiftKappa}}'
         f'{{{sem_zero("%.3f" % _piso_op["kappa_uniform"])}}}',
         # quantas decisoes acima da expectativa uniforme: o excesso que o
         # kappa resume, em unidades que o leitor conta
         f'\\newcommand{{\\pisoAcima}}'
         f'{{{_piso_op["acertos"] - _piso_op["de"] * _piso_op["p_e"]:.1f}}}']
    assert not ct2['qaroush']['ic_cruza_zero'], '⛔ o IC do Qaroush passou a cruzar zero'
    assert ct2['korolkov']['ic_cruza_zero'], '⛔ o IC do Korolkov deixou de cruzar zero: reescrever'
    assert ko['modulo_menos_melhor_membro'] < 0, '⛔ o modulo do Korolkov superou o membro'
    assert va['modulo_menos_melhor_membro'] < 0, '⛔ o modulo superou o melhor membro: reescrever a prosa'
    assert prov['n_operacoes_das_15'] + 1 == prov['n_operacoes_da_triagem'], \
        '⛔ a diferenca entre 16 e 15 deixou de ser so o `si`: reescrever a taxonomia'
    assert val['n_com_pdf'] == prov['n_trabalhos_das_15'], \
        ('⛔ ha trabalho-fonte sem leitura integral (%d lidos de %d): reescrever a prosa'
         % (val['n_com_pdf'], prov['n_trabalhos_das_15']))
    assert sub['por_linha']['controle_identicas']['separa_do_acaso'], \
        '⛔ o controle de implementacoes identicas parou de separar do acaso: o teste nao discrimina'
    assert not sub['por_linha']['controle_sorteio']['separa_do_acaso'], \
        '⛔ o sorteio passou a separar do acaso: o teste esta quebrado'
    assert all(len(v['tipos_abaixo_de_50']) == v['n_significativos']
               for v in inv['por_operacao'].values()), \
        '⛔ ha celula abaixo do acaso que NAO e significativa: a frase da 4.1 cai'
    assert abs(mch['dif'] - (mch['liqe'] - mch['implantada'])) < 1e-9, \
        '⛔ a diferenca da manchete nao fecha com os dois pontos'
    assert tab4['LIQE']['DOVER_bate'] and tab4['SIFT+BoVW']['DOVER_bate'], \
        '⛔ a tabela 4 deixou de reproduzir a fonte do DOVER-T'
    assert esc['clusters_que_SATURAM_o_proprio_tamanho'] == esc['n_clusters'], \
        '⛔ deixou de valer que as quatorze escolhem todos os membros: reescrever a 4.5'
    assert eff['n_operacoes'] == 15 and eff['posto_dos_escores_crus'] < 15, \
        '⛔ o posto das quinze mudou: reescrever a frase da dependencia'
    assert cas3['McNemar_pareado_nos_mesmos_42'][
        'operacao_completa (22) vs so_o_casamento (12)']['separa_a_005'], \
        '⛔ o contraste 22 x 12 deixou de separar: a frase da discussao cai'
    assert not cas3['McNemar_pareado_nos_mesmos_42'][
        'operacao_completa (22) vs controle_casado (16)']['separa_a_005'], \
        '⛔ 22 x 16 passou a separar: a frase antiga poderia voltar'
    # ⛔ a assercao ERRADA que eu escrevi aqui exigia o mesmo n nas duas familias, e ela
    # vinha de uma populacao que incluia o `sobel_cv`, fora do inventario. O invariante
    # certo e outro: a conta do piso tem de bater com o que o CORPO ja imprime.
    assert pd2['operacoes']['n'] == len(natab), \
        '⛔ o piso conta %d operacoes e o corpo imprime %d' % (pd2['operacoes']['n'], len(natab))
    assert pd2['operacoes']['passam'] == sum(1 for v in natab.values() if v['passa']), \
        '⛔ o piso e o corpo discordam de quantas passam'
    assert mtip['os oito tipos']['invertem'] == 15, \
        '⛔ deixou de valer que as quinze invertem com os oito tipos'
    assert rei['reimplementacao']['media'] < rei['pior_modelo_publicado'], \
        '⛔ a reimplementacao passou o pior modelo: a frase da 4.2 cai'
    assert par['pares'] == 800, '⛔ mudou o numero de pares do mecanismo'
    assert abs(cla['controle_duplicata_exata']['kappa'] - 1.0) < 1e-9, \
        '⛔ o controle da duplicata saiu do teto: a conta de concordancia esta errada'
    assert tip['classe_de_sumarizacao']['quantas_ficam_abaixo_da_implantada'] > 0, \
        '⛔ a implantada virou o pior da classe: a frase da ponte cai'
    assert blo['celulas_abaixo_do_acaso'] == 35 and \
        blo['significativas_sob_o_bloco_de_segmento'] < blo['celulas_abaixo_do_acaso'], \
        '⛔ mudou a conta do bloco: reescrever a frase da 4.1'
    # ⛔ a escada das unidades tem de continuar MONOTONICA: quanto mais alta a unidade,
    #    menos celulas sobrevivem. Se inverter, a frase da 4.2 que a descreve cai.
    assert top['significativas_sob_o_bloco_de_topico_12'] \
        <= blo['significativas_sob_o_bloco_de_segmento'] \
        <= blo['significativas_sob_o_binomial_antigo'], \
        '⛔ a escada par > segmento > topico inverteu: reescrever a frase da 4.2'
    # ⭐ o que o artigo afirma NAO depender da unidade: as celulas de 0 de 100.
    #    Se uma cair, a frase «sobrevivem nas tres unidades» vira falsa.
    assert top['celulas_perfeitas_que_sobrevivem'] == top['celulas_perfeitas_0_de_100'], \
        '⛔ uma celula de 0 de 100 deixou de sobreviver: a frase da 4.2 afirma demais'
    # ⛔ 22/09: o corpo declara teste UNILATERAL e a conta que o justifica. Se a cauda
    #    mudar, as 11 celulas mudam e a frase da 4.2 passa a afirmar o que nao se fez.
    assert top['lateralidade']['o_unilateral_passa_o_primeiro_corte'] and \
        not top['lateralidade']['um_bilateral_simetrico_passaria'], \
        '⛔ mudou a lateralidade do teste: reescrever a frase da 4.2'
    # ⛔ a frase da 4.2 e da discussao diz que o ruido e O UNICO tipo que adiciona
    #    energia. Se outro passar a adicionar, as duas frases caem juntas.
    assert [k for k, v in ene.items() if v['adiciona_energia']] == ['noise'], \
        '⛔ mudou quais tipos adicionam energia: reescrever a 4.2 e a discussao'
    # ⛔ 22/09 (parecer v2): o bloco de topico da manchete TEM de ser o fundido, e a
    #    fusao TEM de nao carregar o veredito. Se o sem fundir passasse a incluir zero,
    #    a frase da 4.1 que diz «a escolha nao carrega o resultado» viraria falsa.
    _u = mch['as_tres_unidades']
    assert _u['bloco_de_topico']['n_blocos'] == top['n_blocos_principal'], \
        '⛔ a manchete e a 4.2 discordam de quantos blocos de topico existem'
    assert _u['a_fusao_muda_o_veredito']['ambos_excluem_zero'] and \
        not _u['a_fusao_muda_o_veredito']['veredito_muda'], \
        '⛔ a fusao dos dois rotulos passou a carregar o veredito: reescrever a 4.1'
    assert dez['n'] == 17 and dez['abaixo_da_implantada'] == 8 \
        and sorted(dez['fora_do_inventario_direcional']) == ['qaroush_movimento', 'sobel_cv'], \
        '⛔ mudou a composicao dos dezessete: reescrever a frase da 4.2'
    assert not srf['surf_instanciavel'], \
        '⛔ o SURF passou a existir nesta instalacao: a frase do M12 ficou falsa'
    assert not fin['linhas_que_mudam_de_veredito'], \
        '⛔ a fusao passou a mudar a elegibilidade: reescrever a 4.5'
    assert not fus['linhas_que_mudam_de_veredito'], \
        '⛔ a fusao das fontes passou a mudar o veredito da aplicacao: reescrever a 4.6'
    assert au['autonomas'] == 1, '⛔ mudou o numero de autonomas: reescrever a prosa'
    # ⛔ 22/09: as tres categorias de validacao TEM de somar as fontes lidas.
    assert (len(val['validam_a_propriedade_que_nomeiam'])
            + len(val['avaliam_so_o_resumo'])) <= val['n_com_pdf'], \
        '⛔ as categorias de validacao somam mais que as fontes lidas'
    # ⚠️ as duas regras publicadas TEM de ficar abaixo da media, senao a frase da prosa cai
    assert nb < media, '⛔ o naive Bayes do Ke superou a media: reescrever a prosa'
    # ⭐ 21/09: as macros da TAXONOMIA DE CLASSES, pedida pelo [co-author].
    # ⛔ Nenhum numero da prosa da conclusao e digitado: todos saem daqui.
    _tx = json.load(open(QB / 'classes_contra_o_testbed.json'))
    # ⭐ 21/09: quantos sumarizadores do acervo computam CADA descritor da classe 2. O
    # e-mail do orientador nomeia «SIFT, SURF, ORB agregados por BoVW», e o testbed
    # instancia so o SIFT: sem estes numeros o leitor que procura os outros dois nao acha
    # nem o numero nem o motivo. ⚠️ Sao do mesmo varrido de 21/09 que da as classes.
    _sw = json.load(open(QB / 'taxonomia_das_classes.json'))
    _sumar = {k: v for k, v in _sw['por_pdf'].items() if v['e_sumarizador']}

    def _quem(termo):
        return {k for k, v in _sumar.items()
                for hits in v['classes'].values() if termo in hits}

    def _quantos(termo):
        return len(_quem(termo))

    # ⛔ 21/09, achado da revisao: 31 + 6 + 3 = 40, que e EXATAMENTE o total da classe 2.
    # A coincidencia convida a ler os tres descritores como PARTICAO da classe, e eles nao
    # sao: a uniao e 33, cinco trabalhos usam mais de um, e sete estao na classe sem
    # nomear nenhum dos tres. Sem este numero a soma vira uma inferencia falsa.
    _uniao_desc = len(_quem('sift') | _quem('surf') | _quem('orb/brief'))
    _c4 = json.load(open(QB / 'classe4_proxies_profundos.json'))
    _PAL = {0: 'none', 1: 'one', 2: 'two', 3: 'three'}

    def _n(x):
        """numero por extenso ate tres, algarismo dai em diante. Contagem pequena por
        extenso e a convencao do proprio artigo, e «1 usa» leria mal na frase."""
        return _PAL.get(x, str(x))

    _pb = json.load(open(QB / 'classe4_na_bancada_pareada.json'))['por_operacao']
    _pc = _tx['por_classe']
    L += [f'\\newcommand{{\\taxAcervo}}{{{_tx["n_pdfs_no_acervo"]}}}',
          f'\\newcommand{{\\taxSumarizadores}}{{{_tx["n_sumarizadores"]}}}',
          f'\\newcommand{{\\taxCUm}}{{{_n(_pc["C1"]["trabalhos_na_literatura"])}}}',
          f'\\newcommand{{\\taxCDois}}{{{_n(_pc["C2"]["trabalhos_na_literatura"])}}}',
          f'\\newcommand{{\\taxCTres}}{{{_n(_pc["C3"]["trabalhos_na_literatura"])}}}',
          f'\\newcommand{{\\taxCQuatro}}{{{_n(_pc["C4"]["trabalhos_na_literatura"])}}}',
          f'\\newcommand{{\\taxOpsCUm}}{{{_pc["C1"]["operacoes_instanciadas_no_testbed"]}}}',
         f'\\newcommand{{\\descSift}}{{{_quantos("sift")}}}',
         f'\\newcommand{{\\descSurf}}{{{_quantos("surf")}}}',
         f'\\newcommand{{\\descOrb}}{{{_quantos("orb/brief")}}}',
         f'\\newcommand{{\\descUniao}}{{{_uniao_desc}}}',
         # ⛔ 21/09: SEM ESTAS DUAS o leitor soma as colunas da taxonomia (51+40+1+24=116)
         # contra um total de 86 e conclui que os numeros estao errados. As classes NAO sao
         # exclusivas, e a revisao do artigo pegou isso antes do revisor.
         f'\\newcommand{{\\taxMultiplas}}{{{_tx["⭐_SOBREPOSICAO_ENTRE_CLASSES"]["usam_mais_de_uma"]}}}',
         f'\\newcommand{{\\taxNenhuma}}{{{_tx["⭐_SOBREPOSICAO_ENTRE_CLASSES"]["usam_nenhuma"]}}}',
          f'\\newcommand{{\\taxCoerKappa}}'
          + '{' + f'{_c4["piso_in_domain"]["deep_coerencia"]["kappa"]:.3f}'.replace('0.', '.')
          + '}',
          f'\\newcommand{{\\taxNormaJusante}}'
          f'{{{_c4["jusante_contra_o_sift_implantado"]["deep_norma"]["pct"]:.1f}}}',
          f'\\newcommand{{\\taxCentroideDecide}}'
          f'{{{_c4["jusante_contra_o_sift_implantado"]["deep_centroide"]["n"]}}}',
          f'\\newcommand{{\\taxNormaPar}}{{{_pb["deep_norma"]["media"]:.1f}}}',
          f'\\newcommand{{\\taxCoerPar}}{{{_pb["deep_coerencia"]["media"]:.1f}}}',
          f'\\newcommand{{\\taxNormaInverte}}'
          f'{{{len(_pb["deep_norma"]["inverte_em"])}}}',
          f'\\newcommand{{\\taxCoerInverte}}'
          f'{{{len(_pb["deep_coerencia"]["inverte_em"])}}}',
          ]
    # ⭐ 27/09 (parecer, classe 4): a distancia ao centroide deixou de ser «identity on a
    # pair». A copia degradada entra no cluster REAL do original (pre-registro e6ef9e3 no
    # benchmark, resultado 6c1f6ef). O controle com membros de OUTROS topicos e
    # exploratorio e vai declarado assim: e ele que diz quanto da preferencia e do cluster.
    _cp = json.load(open(QB / 'classe4_centroide_na_bancada.json'))
    _cpp = _cp['primaria_centroide_com_todos_os_membros_mais_a_copia']
    _cc = json.load(open(QB / 'classe4_centroide_controles.json'))
    _cca = _cc['2_centroide_com_membros_de_outros_topicos']
    _ccd = _cc['diferenca_pareada_real_menos_outros_topicos']

    MODELOS_TAB4 = {'liqe', 'topiq_nr', 'musiq', 'qualiclip', 'arniqa', 'dbcnn', 'niqe',
                     'clipiqa_plus', 'hyperiqa', 'clipiqa', 'brisque'}
    _achados = {l['nome'] for l in json.load(open(QB / 'TABELA_FINAL.json'))['linhas']} & MODELOS_TAB4
    assert _achados == MODELOS_TAB4, 'faltam modelos da Tabela 4: %s' % (MODELOS_TAB4 - _achados)

    def _acima_do_centroide():
        import statistics as _s
        _a = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
        _d = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
        ops = [k for k in _a if k in _d]
        assert len(ops) == 15, 'esperava as quinze operacoes, achei %d' % len(ops)
        med = {k: _s.mean([x for x in _d[k]['acuracia_por_tipo'] if x is not None]) for k in ops}
        return sum(v > _cpp['media'] for v in med.values())

    def _ic1(par):
        return f'[{par[0]:.1f},\\,{par[1]:.1f}]'
    # ⭐ 28/09 (parecer): a Tabela 3 saiu; o que so ela mostrava vai para a prosa da 4.1.
    _kad = json.load(open(QB / 'analise_kadid.json'))['por_metodo']['dinov2']
    _kon = json.load(open(QB / 'analise_koniq.json'))['por_metodo']['dinov2']
    _mn = min(_kad['rho_orientado'], _kon['rho'])
    _np = _c4['piso_in_domain']['deep_norma']['kappa']
    def _sinal(x):
        t = ('%.3f' % x).replace('0.', '.')
        return '\\ensuremath{%s}' % t if x < 0 else t
    L += [f'\\newcommand{{\\taxNormaExt}}{{{_sinal(_mn)}}}',
          f'\\newcommand{{\\taxNormaPiso}}{{{_sinal(_np)}}}']
    L += [f'\\newcommand{{\\taxCentPar}}{{{_cpp["media"]:.1f}}}',
          f'\\newcommand{{\\taxCentIC}}{{{_ic1(_cpp["ic95_bootstrap_segmentos"])}}}',
          f'\\newcommand{{\\taxCentInverte}}{{{_n(len(_cpp["inverte_em"]))}}}',
          f'\\newcommand{{\\taxCentMin}}{{{min(_cpp["acuracia_por_tipo"]):.1f}}}',
          f'\\newcommand{{\\taxCentOutros}}{{{_cca["media"]:.1f}}}',
          f'\\newcommand{{\\taxCentDif}}{{{_ccd["media_pontos"]:.1f}}}',
          f'\\newcommand{{\\taxCentDifIC}}{{{_ic1(_ccd["ic95_bootstrap_segmentos"])}}}',
          # ⭐ 28/09 (parecer do [author], item 1): «abaixo de todo modelo dedicado» no resumo
          # precisa do minimo da MESMA tabela; o `reiPiorModelo` e de outro experimento.
          # ⛔ a familia «NR-IQA / descritor» do JSON INCLUI o SIFT+BoVW (65,1): filtrar por
          # familia dava 65,1 e poria numero falso no resumo. A lista e a dos onze modelos
          # dedicados da Tabela 4, a mesma da `guarda_tabela_construida`.
          f'\\newcommand{{\\taxModeloMin}}{{{min(l["media"] for l in json.load(open(QB / "TABELA_FINAL.json"))["linhas"] if l["nome"] in MODELOS_TAB4):.1f}}}',
          # ⛔ 28/09 (parecer): «above the median heuristic» so vale para a mediana de 17 (66,0,
          # com sobel_cv e qaroush_ct). Nas QUINZE auditadas a mediana e 74,8, acima do 74,1.
          # O que se afirma e quantas das quinze passam do centroide.
          f'\\newcommand{{\\taxCentAbaixoDe}}{{{dict(enumerate(["none", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen"]))[_acima_do_centroide()]}}}',
          f'\\newcommand{{\\taxCentMeios}}{{{_n(_cc["pares_com_meia_decisao"]["n"])}}}',
          ]

    # ⛔ O RESUMO NAO ALCANCA AS MACROS DA FIGURA. O `\jusMediana` e o `\jusPiso` nascem
    # dentro de `fig_jusante.tex`, que entra por `\input` no meio dos resultados, muito
    # depois do `\abstract`. Usa-los no resumo da «Undefined control sequence» e o numero
    # sai VAZIO no PDF, sem erro visivel na leitura. Por isso eles sao recomputados aqui,
    # da MESMA fonte, e conferidos contra o que a figura imprime: uma fonte so, com guarda.
    import statistics as _st
    import re as _re
    _lado = json.load(open(QB / 'jusante_lado_a_lado.json'))
    _pcts = [x['pct'] for x in _lado['linhas'] if 'sumarizacao' in x['familia']]
    _falt = json.load(open(
        QB / 'jusante_ops_faltantes_caminho_velho.json'))['concordancia_com_sift']
    _nomes_fig = _re.findall(r"'([a-z_0-9]+)': '[^']*'",
                             (SAIDA.parent / 'gera_fig_jusante.py').read_text())
    _pcts += [v['pct'] for n, v in _falt.items() if n in _nomes_fig]
    _med = _st.median(_pcts)
    _piso = _lado['piso_do_acaso_pct']
    # ⭐⭐ A MANCHETE QUE E SOBRE A LITERATURA e nao sobre um modulo: quantas
    # implementacoes publicadas do MESMO criterio produzem quantos resumos DIFERENTES.
    # Ela nao usa modulo de referencia nenhum, e por isso nao pode ser lida como critica
    # a um sumarizador especifico.
    _dis = json.load(open(QB / 'quantos_resumos_distintos_a_classe_produz.json'))
    assert _dis['controle_passou'], \
        '⛔ o controle das identidades declaradas caiu: a manchete de classe nao vale'
    L += [f'\\newcommand{{\\taxJusMediana}}{{{_med:.1f}}}',
          f'\\newcommand{{\\taxJusPiso}}{{{_piso:.1f}}}',
          f'\\newcommand{{\\disOps}}'
          f'{{{_dis["todas_as_operacoes"]["n_operacoes"]}}}',
          f'\\newcommand{{\\disResumos}}'
          f'{{{_dis["todas_as_operacoes"]["n_resumos_distintos"]}}}',
          f'\\newcommand{{\\disClusters}}{{{_dis["clusters_com_discordancia"]}}}']

    # ⛔ e a guarda que impede as duas fontes de divergirem em silencio
    _fig = (SAIDA.parent / 'macros_jusante.tex').read_text(encoding='utf-8')
    _mfig = _re.search(r'newcommand\{\\jusMediana\}\{([0-9.]+)\}', _fig)
    assert _mfig and abs(float(_mfig.group(1)) - _med) < 0.05, \
        '⛔ a mediana do jusante diverge entre a figura e as macros do resumo'

    # ⛔ a prosa afirma que a norma inverte na MAIORIA dos tipos e a coerencia NAO inverte
    # sob ruido. As duas sao previsoes que foram declaradas antes de rodar e confirmadas;
    # se o dado mudar, a frase cai e tem de ser reescrita, nao ajustada no numero.
    assert len(_pb['deep_norma']['inverte_em']) >= 5, \
        '⛔ a norma deixou de inverter na maioria dos tipos: a frase da classe 4 cai'
    assert 'noise' not in _pb['deep_coerencia']['inverte_em'], \
        '⛔ a coerencia passou a inverter sob ruido: a excecao declarada cai'

    # ⛔ a frase da conclusao afirma que a classe 3 e a MENOS usada, e que as outras tres
    # sao as que a bancada reprova. Se a varredura mudar e isso deixar de valer, a frase
    # cai e tem de ser reescrita, nao corrigida no numero.
    assert _pc['C3']['trabalhos_na_literatura'] < min(
        _pc[c]['trabalhos_na_literatura'] for c in ('C1', 'C2', 'C4')), \
        '⛔ a classe 3 deixou de ser a menos usada: a frase da conclusao cai'
    # ⛔ e a excecao declarada tem de continuar existindo: se a coerencia parar de passar
    # o piso, a frase «com uma excecao carregada em aberto» vira falsa por omissao
    assert _c4['piso_in_domain']['deep_coerencia']['passa'], \
        '⛔ a coerencia deixou de passar o piso: a excecao da conclusao cai'

    # ⛔ a conclusao afirma DUAS coisas sobre a classe 3, e as duas tem de valer no dado:
    #   (a) os que passam as duas portas externas sao TODOS vision-language;
    #   (b) o BRISQUE e o NIQE, os classicos estatisticos, REPROVAM a generalizacao.
    # Se qualquer uma cair, a frase cai e tem de ser reescrita, nao ajustada.
    import re as _re
    _tri = (SAIDA.parent / "tab_screening.tex").read_text(encoding="utf-8")
    _linhas = [l for l in _tri.split('\n') if '&' in l and '\\hd{' not in l]
    _eleg, _reprovam = [], {}
    for _l in _linhas:
        _nomes = _re.findall(r'\\textbf\{([^}]*)\}', _l)
        if not _nomes:
            continue
        _nome = _nomes[0]
        _cols = [c.strip() for c in _l.split('&')]
        _ult = _cols[-1].replace('\\\\', '').strip()
        if 'yes' in _ult:
            _eleg.append(_nome)
        _reprovam[_re.sub(r'\\[a-zA-Z]+|[{}$]', '', _nome).strip()] = _ult
    # tambem as linhas sem negrito no nome
    for _l in _linhas:
        _cols = [c.strip() for c in _l.split('&')]
        if len(_cols) < 7:
            continue
        _nome = _re.sub(r'\\rowcolor\{[^}]*\}|\\[a-zA-Z]+|[{}$]', '', _cols[0]).strip()
        if _nome:
            _reprovam.setdefault(_nome, _cols[-1].replace('\\\\', '').strip())

    _VL = ('LIQE', 'QualiCLIP', 'CLIP-IQA')
    assert _eleg, '⛔ nao consegui ler nenhum elegivel da tabela de triagem'
    assert all(any(v in e for v in _VL) for e in _eleg), \
        '⛔ um elegivel deixou de ser vision-language: a frase da classe 3 cai (%s)' % _eleg
    for _m in ('NIQE', 'BRISQUE'):
        _v = next((v for k, v in _reprovam.items() if k.upper() == _m), None)
        assert _v is not None, '⛔ nao achei a linha do %s na triagem' % _m
        assert 'no' in _v and 'yes' not in _v, \
            '⛔ %s passou a ser elegivel: a frase dos classicos cai' % _m

    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(L)} macros -> {SAIDA.name}')
    for x in L:
        print('   ', x)


if __name__ == '__main__':
    main()
