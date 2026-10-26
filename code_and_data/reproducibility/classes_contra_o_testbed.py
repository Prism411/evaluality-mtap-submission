"""⭐⭐ AS QUATRO CLASSES CONTRA O QUE O TESTBED INSTANCIA: onde o artigo esta cheio e
onde esta vazio.

POR QUE EXISTE (21/09/2026). O e-mail do [co-author] pede que a literatura seja
classificada em CLASSES de metodo de qualidade visual, que se escolha um representante
de cada classe, e que a tabela taxonomica mostre quais sumarizadores usam quais classes.
Este script cruza as duas metades da pergunta:
  (a) quantos trabalhos da literatura usam cada classe  -> `taxonomia_das_classes.json`
  (b) quantas operacoes o nosso testbed instancia em cada classe -> declarado aqui

⛔ A TAXONOMIA E DELE, e fica declarada como tal no artigo. As quatro classes sao as do
e-mail de 21/09/2026.

⚠️ O QUE ESTE SCRIPT NAO E. Ele nao mede nada novo: recombina a varredura com o
inventario do artigo. O numero de trabalhos por classe vem de varredura por termo, cuja
precisao medida e 0,63, e portanto e RASTREIO. O numero de operacoes por classe vem do
inventario, que foi conferido fonte a fonte, e esse e firme. As duas colunas nao tem o
mesmo estatuto e a legenda diz isso.
"""
import json
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
SAIDA = H / 'classes_contra_o_testbed.json'

# ⭐ As 16 operacoes auditadas, com a classe de cada uma. A atribuicao e por LEITURA do
# que a operacao computa, nao por termo: todas as dezesseis sao estatisticas de sinal ou
# de pixel calculadas num quadro, que e a definicao da classe 1 no e-mail.
OPERACOES_POR_CLASSE = {
    'C1': ['Averaged aesthetics (3)', 'Colourfulness (Hasler)', 'Colourfulness (Ke)',
           'Composite of five', 'Contrast', 'Edge distribution', 'Entropy',
           'GLCM contrast', 'Gradient magnitude', 'Gradient orientation',
           'Grey-level dispersion', 'Hue count', 'Laplacian variance', 'Saliency area',
           'Saturation', 'Spatial information'],
    'C2': ['SIFT+BoVW (deployed)', 'Keypoint density', '19 CNN+BoVW (ablation)'],
    'C3': ['BRISQUE', 'NIQE', 'DBCNN', 'HyperIQA', 'MUSIQ', 'TOPIQ', 'CLIP-IQA',
           'CLIP-IQA+', 'QualiCLIP', 'LIQE'],
    # ⛔ 21/09, fim do dia: esta lista estava VAZIA e o arquivo era de 13h26, ANTES de a
    # classe 4 ser instanciada (`classe4_proxies_profundos.json`, 13h53, e a Tabela 3 do
    # corpo, 14h20). A tabela do artigo saia com «0» na coluna de operacoes e, na coluna
    # ao lado, NOMEAVA um representante — contradicao na mesma linha —, e a legenda dizia
    # «ate esta versao, nenhum representante no testbed», que deixara de ser verdade.
    # ⚠️ Os tres entram como INSTANCIADOS e nenhum carrega veredito de triagem: dois deles
    # nao sao avaliaveis nas bancadas externas, e o motivo e de CONSTRUCAO, nao de
    # implementacao. Esse e o achado da classe 4, e a coluna passa a refleti-lo.
    'C4': ['Feature-vector norm', 'Frame coherence', 'Distance to the cluster centre'],
}

# ⚠️ instanciadas mas SEM veredito de triagem, e o motivo de cada uma
SEM_VEREDITO_DE_TRIAGEM = {
    'Feature-vector norm': 'nenhuma fonte do acervo a computa; construcao nossa',
    'Frame coherence': 'precisa de varios quadros, e a bancada externa pontua imagem',
    'Distance to the cluster centre': 'e identidade num par, e 36 dos 42 clusters tem dois',
}

# ⚠️ o que esta no artigo com papel de CONTROLE, e portanto fora de toda contagem
CONTROLE_DIAGNOSTICO = {'C4': ['DINOv2 (patch-token norm)', 'ResNet-50 (pooled norm)']}

NOME_LONGO = {
    'C1': 'Heuristicas de baixo nivel (sinais/pixels)',
    'C2': 'BoVW / contagem de recursos (hand-crafted)',
    'C3': 'NR-IQA estatistico classico',
    'C4': 'Proxies de diversidade/representatividade profunda (CNN/ViT)',
}

CHAVE_VARREDURA = {
    'C1': 'C1_heuristicas_de_baixo_nivel',
    'C2': 'C2_bovw_e_contagem_artesanal',
    'C3': 'C3_nriqa_estatistico_classico',
    'C4': 'C4_proxy_profundo_de_selecao',
}


def main():
    tx = json.load(open(H / 'taxonomia_das_classes.json'))
    pp = {k: v for k, v in tx['por_pdf'].items() if v['e_sumarizador']}
    n_sum = len(pp)

    def conta(classe, termos=None):
        ch = CHAVE_VARREDURA[classe]
        out = []
        for k, v in pp.items():
            hits = v['classes'].get(ch, [])
            if not hits:
                continue
            if termos is None or set(hits) & set(termos):
                out.append(k)
        return out

    # ⛔ Na classe 4 a contagem crua NAO serve. O termo `cosseno` casa com similaridade
    # de cosseno usada para REDUNDANCIA e agrupamento, que nao e escore de qualidade, e
    # sozinho responde pela maioria dos casos. A contagem defensavel exige o termo que
    # nomeia a selecao: distancia ao centroide, ou representatividade.
    c4_cru = conta('C4')
    c4_firme = conta('C4', ['centroide', 'representatividade', 'representativid'])
    c4_ambiguo = sorted(set(c4_cru) - set(c4_firme))

    linhas = {}
    for c in ['C1', 'C2', 'C3', 'C4']:
        trabalhos = c4_firme if c == 'C4' else conta(c)
        linhas[c] = {
            'classe': NOME_LONGO[c],
            'trabalhos_na_literatura': len(trabalhos),
            'de_sumarizadores_lidos': n_sum,
            'operacoes_instanciadas_no_testbed': len(OPERACOES_POR_CLASSE[c]),
            'operacoes': OPERACOES_POR_CLASSE[c],
            'controle_diagnostico_fora_da_contagem': CONTROLE_DIAGNOSTICO.get(c, []),
            'tem_representante': bool(OPERACOES_POR_CLASSE[c]),
            # ⚠️ instanciada NAO implica triada: a classe 4 entra com tres representantes
            # e nenhum veredito, e o motivo fica ao lado de cada uma.
            'instanciadas_sem_veredito_de_triagem': {
                o: SEM_VEREDITO_DE_TRIAGEM[o] for o in OPERACOES_POR_CLASSE[c]
                if o in SEM_VEREDITO_DE_TRIAGEM},
        }

    # ⭐ 21/09: QUANTAS CLASSES CADA TRABALHO USA. Sem isto a tabela do artigo publica
    # 51 + 40 + 1 + 24 = 116 contra um total de 86, e o leitor que somar conclui que os
    # numeros estao errados. As classes NAO sao exclusivas: um trabalho pode computar uma
    # heuristica de baixo nivel E um proxy profundo, e 40 dos 86 fazem isso.
    from collections import Counter as _C
    _q = _C()
    for _k, _v in pp.items():
        _n = 0
        for _c in ('C1', 'C2', 'C3', 'C4'):
            _h = _v['classes'].get(CHAVE_VARREDURA[_c], [])
            if _c == 'C4':
                _h = [x for x in _h
                      if x in ('centroide', 'representatividade', 'representativid')]
            _n += bool(_h)
        _q[_n] += 1
    sobreposicao = {'por_quantas_classes': {str(k): _q[k] for k in sorted(_q)},
                    'usam_mais_de_uma': sum(v for k, v in _q.items() if k > 1),
                    'usam_nenhuma': _q[0],
                    'soma_das_colunas': sum(linhas[c]['trabalhos_na_literatura']
                                            for c in ('C1', 'C2', 'C3', 'C4')),
                    'total_de_sumarizadores': n_sum,
                    '⚠️_por_que_a_soma_excede': (
                        'as classes nao sao exclusivas: um trabalho pode computar mais de '
                        'uma. Sem esta linha o leitor soma as colunas e conclui erro.')}

    vazias = [c for c, v in linhas.items() if not v['tem_representante']]

    out = {
        '_o_que_e': __doc__.strip(),
        'taxonomia_de': '[co-author], e-mail de 21/09/2026; nao e nossa',
        'n_pdfs_no_acervo': tx['n_pdfs'],
        'n_sumarizadores': n_sum,
        'por_classe': linhas,
        '⭐_CLASSES_SEM_REPRESENTANTE': vazias,
        '⭐_SOBREPOSICAO_ENTRE_CLASSES': sobreposicao,

        '⭐⭐_o_achado_estrutural': (
            'as DEZESSEIS operacoes TRIADAS sao TODAS da classe 1. O artigo audita uma '
            'classe em profundidade, tem a classe 2 como caso implantado, a classe 3 como '
            'conjunto de candidatos, e a classe 4 instanciada com {} representantes que '
            'NENHUM eixo externo consegue triar. E por isso que a auditoria se le como '
            'sendo de um trabalho so: nao e falta de operacao, e falta de CLASSE.'
            ).format(len(OPERACOES_POR_CLASSE['C4'])),
        # ⛔ a redacao anterior dizia «e a classe 4 VAZIA», escrita as 13h26, antes de a
        # classe 4 ser instanciada as 13h53 e medida na Tabela 3 as 14h20. Ficou falsa no
        # mesmo dia, e era o JSON que a tabela do corpo le.

        '⭐⭐_a_desconexao_por_classe': {
            'C3_entre_sumarizadores': len(conta('C3')),
            'quais': conta('C3'),
            'leitura': ('de {} sumarizadores do acervo, {} cita uma metrica NR-IQA '
                        'dedicada. A literatura usa as classes 1, 2 e 4 e praticamente '
                        'nunca a 3, que e a unica desenhada para medir qualidade'
                        ).format(n_sum, len(conta('C3'))),
        },

        '⛔_a_norma_do_vetor_nao_tem_fonte': {
            'ocorrencias_no_acervo_inteiro': len(
                [k for k, v in tx['por_pdf'].items()
                 if 'norma_do_vetor' in v['classes'].get(CHAVE_VARREDURA['C4'], [])]),
            'consequencia': ('o representante da classe 4 que o nosso codigo ja tem '
                             '(norma da feicao, em DINOv2 e ResNet-50) NAO corresponde a '
                             'nenhum uso declarado na literatura varrida. Ele e construcao '
                             'NOSSA e vai declarado como tal, no mesmo padrao com que o '
                             'artigo ja declara que a media do Gygli e escolha nossa. '
                             'A distancia ao centroide, essa sim, tem lastro'),
        },

        '⚠️_classe_4_contagem': {
            'cru': len(c4_cru),
            'firme_centroide_ou_representatividade': len(c4_firme),
            'ambiguo_so_por_cosseno': len(c4_ambiguo),
            'por_que': ('similaridade de cosseno em sumarizacao serve sobretudo a '
                        'redundancia e agrupamento, que nao e escore de qualidade. '
                        'Contar os dois juntos inflaria a classe'),
        },

        '⚠️_estatuto_das_duas_colunas': (
            'trabalhos por classe vem de varredura por termo, precisao medida 0,63: e '
            'RASTREIO e pede leitura. Operacoes por classe vem do inventario conferido '
            'fonte a fonte: e firme. A legenda da tabela separa as duas'),

        '⚠️_vies_do_acervo': tx['⚠️_vies_declarado'],
    }
    json.dump(out, open(SAIDA, 'w'), indent=1, ensure_ascii=False)

    print(f'=== {n_sum} sumarizadores de {tx["n_pdfs"]} PDF ===\n')
    print(f'{"":4} {"classe":<52} {"literatura":>10} {"testbed":>8}')
    for c, v in linhas.items():
        mark = '🔴' if not v['tem_representante'] else '  '
        print(f'{mark} {c} {v["classe"]:<50} {v["trabalhos_na_literatura"]:>7} '
              f'{v["operacoes_instanciadas_no_testbed"]:>8}')
    print(f'\n⭐ classes sem representante no testbed: {vazias}')
    print(f'⭐ C3 entre sumarizadores: {len(conta("C3"))} de {n_sum}')
    print(f'⛔ "norma do vetor" no acervo inteiro: '
          f'{out["⛔_a_norma_do_vetor_nao_tem_fonte"]["ocorrencias_no_acervo_inteiro"]}')
    print(f'\n📄 {SAIDA.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
