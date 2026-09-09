#!/usr/bin/env python3
"""As macros da secao que fecha «os modulos nao foram reproduzidos como publicados».

Cada fonte que ESPECIFICA uma regra de combinacao teve essa regra implementada e medida na
mesma bancada pareada. Nada aqui e escolha nossa de agregacao: e o que o PDF manda fazer.
"""
import json
import re
from pathlib import Path


# ⛔ `` comia o zero INTERNO: 40.5 virava 4.5.
# Tira so o zero a esquerda do ponto que nao vem depois de digito.
def sem_zero(t):
    return re.sub(r'(?<![0-9])0\.', '.', t)


QB = Path('/dados/Projetos/quality-benchmark')
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
    mch = json.load(open(QB / 'o_bloco_de_segmento_reproduz_um_intervalo_publicado.json'))['manchete']
    exc = json.load(open(QB / 'as_tres_excecoes_do_mecanismo.json'))
    tab4 = json.load(open(QB / 'a_tabela_4_reproduz.json'))['por_metodo']
    AQ = Path(__file__).parent
    r2 = json.load(open(AQ / 'second_revision_reanalysis.json'))['application']['branches']
    r3 = json.load(open(AQ / 'third_revision_reanalysis.json'))['same_frame_same_pooling']
    tec = r2['technical']['liqe_minus_sift']
    cas = r3['regimes']['uniform_1fps_capped10_mean']['liqe_minus_sift']
    esc = json.load(open(QB / 'quantas_escolhas_distintas_por_cluster.json'))
    eff = json.load(open(QB / 'posto_e_m_eff_das_15.json'))
    ref = json.load(open(QB / 'a_sensibilidade_depende_de_quais_referencias.json'))
    cas3 = json.load(open(QB / 'o_casamento_sozinho_move_doze.json'))
    pd2 = json.load(open(QB / 'o_piso_das_duas_familias_na_mesma_convencao.json'))
    mtip = json.load(open(QB / 'a_manchete_depende_de_quais_tipos.json'))['por_cenario']
    rei = json.load(open(QB / 'a_reimplementacao_reproduz_a_falha.json'))
    par = json.load(open(QB / 'a_contagem_reproduz_a_escolha_par_a_par.json'))
    cla = json.load(open(QB / 'a_classe_nao_concorda_consigo.json'))
    tip = json.load(open(QB / 'a_implantada_e_tipica_da_classe.json'))
    ele = json.load(open(QB / 'a_elegibilidade_e_familia_nao_supervisao.json'))
    comb = json.load(open(QB / 'as_combinacoes_COMO_A_LITERATURA_PUBLICA.json'))
    _q = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))
    q15, regra = _q['por_operacao'], _q['regra']
    va = json.load(open(QB / 'o_vascore_do_qaroush_como_a_Eq20_manda.json'))
    ko = json.load(open(QB / 'o_modulo_do_korolkov_nos_11_segmentos.json'))
    du = json.load(open(QB / 'a_concordancia_sem_as_duplicatas.json'))
    ct2 = json.load(open(QB / 'o_contraste_pareado_dos_modulos.json'))
    # ⚠️ estas macros viviam na tab_literatura.tex, que foi para o suplementar; o corpo
    # perdeu as definicoes e o build quebrou em 7 pontos. Vivem aqui agora.
    pz = {x['operacao']: x for x in
          json.load(open(QB / 'o_piso_das_operacoes_isoladas_e_estavel.json'))['por_operacao']}
    tab16 = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    conta = {k: v for k, v in pz.items() if k != 'si'}
    natab = {k: v for k, v in conta.items() if k in tab16}
    PAL = {10: 'ten', 9: 'nine', 6: 'Six', 5: 'Five'}

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
         f'\\newcommand{{\\pisoPop}}{{{PAL[len(conta)].lower()}}}',
         f'\\newcommand{{\\pisoPassam}}{{{PAL[sum(1 for v in conta.values() if v["passa"])]}}}',
         f'\\newcommand{{\\pisoTabPop}}{{{PAL[len(natab)].lower()}}}',
         f'\\newcommand{{\\pisoTabPassam}}{{{PAL[sum(1 for v in natab.values() if v["passa"])]}}}',
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
         # ⛔ a contagem das fontes vinha digitada em cinco lugares do corpo. Ela e
         # medida: 16 = as 15 da literatura de sumarizacao + o `si`, que vem da ITU-T.
         f'\\newcommand{{\\fontesOperacoes}}{{{POREXT[prov["n_operacoes_da_triagem"]]}}}',
         f'\\newcommand{{\\fontesDaLiteratura}}{{{POREXT[prov["n_operacoes_das_15"]]}}}',
         f'\\newcommand{{\\fontesTrabalhos}}{{{POREXT[prov["n_trabalhos_das_15"]]}}}',
         # ⛔ a concordancia que SOBRA depois da substituicao, contra o acaso dos 42
         # clusters. Sem isto o «muda 22 de 42» deixa em aberto o que os outros 20 sao.
         f'\\newcommand{{\\subResta}}{{{POREXT[sub["por_linha"]["liqe_x_implantada"]["acertos"]]}}}',
         f'\\newcommand{{\\subPct}}{{{sub["por_linha"]["liqe_x_implantada"]["pct"]:.1f}}}',
         f'\\newcommand{{\\subAcaso}}{{{100 * sub["acaso_medio"]:.1f}}}',
         f'\\newcommand{{\\subKappa}}{{{sem_zero("%.3f" % sub["por_linha"]["liqe_x_implantada"]["kappa_contra_o_acaso"])}}}',
         f'\\newcommand{{\\subIC}}{{[{sub["por_linha"]["liqe_x_implantada"]["ic_bloco_de_topico"][0]:.1f}, '
         f'{sub["por_linha"]["liqe_x_implantada"]["ic_bloco_de_topico"][1]:.1f}]}}',
         # ⛔ «inverte em pelo menos um tipo» e quase certo por acaso. O que separa e que
         # TODA celula abaixo do acaso e significativa, e a moeda de controle nao acumula.
         f'\\newcommand{{\\invCelulas}}{{{sum(len(v["tipos_abaixo_de_50"]) for v in inv["por_operacao"].values())}}}',
         f'\\newcommand{{\\invTestes}}{{{inv["n_testes"]}}}',
         f'\\newcommand{{\\invMoeda}}{{{"none" if inv["controle_da_moeda"]["quantas_acumulam_significancia"] == 0 else POREXT[inv["controle_da_moeda"]["quantas_acumulam_significancia"]]}}}',
         # ⭐ o mesmo teste na outra familia: sem ele a leitura e de um lado so
         f'\\newcommand{{\\invModelosLimpos}}{{{POREXT[inv["a_outra_familia"]["sem_nenhum_tipo_abaixo"]]}}}',
         f'\\newcommand{{\\invModelos}}{{{POREXT[inv["a_outra_familia"]["n_modelos"]]}}}',
         # ⛔ BURACO MEDIDO EM 08/09: os tres numeros da manchete estavam DIGITADOS, e
         # trocar o +34,4 por +31,4 passava por todas as guardas. Agora vem do arquivo,
         # e o IC ao lado ja vem do mesmo lugar pela guarda de unidade.
         f'\\newcommand{{\\mchImplantada}}{{{mch["implantada"]:.1f}}}',
         f'\\newcommand{{\\mchLiqe}}{{{mch["liqe"]:.1f}}}',
         f'\\newcommand{{\\mchDif}}{{{mch["dif"]:.1f}}}',
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
         f'\\newcommand{{\\resRuido}}{{{POREXT[sum(1 for v in inv["por_operacao"].values() if (lambda a: a is not None and a < 50)(v["acuracia_por_tipo"].get("noise")))]}}}']
    assert not ct2['qaroush']['ic_cruza_zero'], '⛔ o IC do Qaroush passou a cruzar zero'
    assert ct2['korolkov']['ic_cruza_zero'], '⛔ o IC do Korolkov deixou de cruzar zero: reescrever'
    assert ko['modulo_menos_melhor_membro'] < 0, '⛔ o modulo do Korolkov superou o membro'
    assert va['modulo_menos_melhor_membro'] < 0, '⛔ o modulo superou o melhor membro: reescrever a prosa'
    assert prov['n_operacoes_das_15'] + 1 == prov['n_operacoes_da_triagem'], \
        '⛔ a diferenca entre 16 e 15 deixou de ser so o `si`: reescrever a taxonomia'
    assert val['n_com_pdf'] + 1 == prov['n_trabalhos_das_15'], \
        '⛔ mudou quantas fontes foram lidas na integra: reescrever a prosa'
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
    assert au['autonomas'] == 1, '⛔ mudou o numero de autonomas: reescrever a prosa'
    # ⚠️ as duas regras publicadas TEM de ficar abaixo da media, senao a frase da prosa cai
    assert nb < media, '⛔ o naive Bayes do Ke superou a media: reescrever a prosa'
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(L)} macros -> {SAIDA.name}')
    for x in L:
        print('   ', x)


if __name__ == '__main__':
    main()
