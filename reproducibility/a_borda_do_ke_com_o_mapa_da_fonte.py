"""⛔⛔ A DISTRIBUICAO DE BORDAS DO KE, COM O MAPA QUE A FONTE ESPECIFICA.

POR QUE EXISTE (13/09/2026, apos o segundo parecer do MTAP). Um revisor observou que a
nossa `ke_edge_distribution` projeta a magnitude de SOBEL sobre a imagem em cinza, e que a
fonte especifica outra coisa. ⭐ Conferido no PDF (`ke2006highlevel.pdf`, secao 4.1), ele
tem razao, e o texto da fonte e explicito:

  «we apply a 3x3 Laplacian filter with alpha = 0.2 to the image, and take its absolute
   value ... For color images, we apply the filter to each of the red, green, and blue
   channels separately and then take the mean across the channels. Finally, we resize
   Laplacian image size to 100x100 and normalize the image sum to 1»

  «The area of the bounding box is calculated by projecting THE LAPLACIAN IMAGE L onto
   the x and y axes independently ... the quality of the image qa is 1 - wx*wy»

✅ O QUE JA ESTAVA CERTO: a formula `1 - wx*wy` e a massa de 98 %.
⛔ O QUE DIVERGE: o MAPA. Sobel de 1a ordem em cinza, tamanho nativo, sem normalizar,
   contra Laplaciano de 2a ordem por canal RGB, 100x100, soma 1.

⚠️ E ISSO IMPORTA porque esta e a operacao de MAIOR sensibilidade entre as heuristicas.
Se o veredito da porta depender do mapa, a linha nao pode ser reportada como reproducao.

📌 PRE-CONDICAO: reproduzir a sensibilidade publicada da versao Sobel (0,298 e 9/25) ANTES
de comparar. Sem isso eu nao sei se o meu protocolo e o do artigo.

⭐ PREVISOES DECLARADAS ANTES DE RODAR:
 1. As duas versoes correlacionam alto entre si (ambas medem concentracao de borda).
 2. A sensibilidade MUDA, porque o Laplaciano e de 2a ordem e responde a ruido muito
    mais que o Sobel.
 3. O VEREDITO da porta (reprova em sensibilidade) NAO muda, porque 0,298 esta longe
    de 0,50.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

H = Path('/dados/Projetos/quality-benchmark')
sys.path.insert(0, str(H))
import ops_da_literatura as OPS  # noqa: E402

IMGS = H / 'data/kadid10k/kadid10k/images'
PUBLICADO = {'media': 0.298, 'tipos': 9}


def largura98(proj):
    t = proj.sum()
    if t <= 0:
        return 1.0
    c = np.cumsum(proj) / t
    lo = int(np.searchsorted(c, 0.01))
    hi = int(np.searchsorted(c, 0.99))
    return max(hi - lo, 1) / len(proj)


def ke_borda_fiel(bgr):
    """O mapa que a fonte especifica, elo a elo."""
    b = bgr.astype(np.float64)
    # ⭐ Laplaciano 3x3 com alpha = 0.2: a forma padrao da MATLAB `fspecial('laplacian')`,
    # que e o contexto em que o artigo de 2006 escreve alpha.
    a = 0.2
    k = np.array([[a, 1 - a, a],
                  [1 - a, -4.0, 1 - a],
                  [a, 1 - a, a]], dtype=np.float64) * (4.0 / (a + 1.0))
    canais = [np.abs(cv2.filter2D(b[:, :, c], cv2.CV_64F, k)) for c in range(3)]
    L = np.mean(canais, axis=0)            # media entre os canais RGB
    L = cv2.resize(L, (100, 100))          # resize 100x100
    s = L.sum()
    if s > 0:
        L = L / s                          # normaliza a soma para 1
    wx = largura98(L.sum(axis=0))
    wy = largura98(L.sum(axis=1))
    return float(1.0 - wx * wy)


def sensibilidade(escores, df):
    """O protocolo DO ARTIGO, identificado por reproducao em 13/09.

    ⛔ A primeira versao deste script usou |rho| e deu 0,774 contra os 0,298 publicados.
    Testados os cinco candidatos, o que reproduz e: rho de Spearman contra o NIVEL de
    degradacao, dentro de cada referencia, ORIENTADO pela direcao declarada da operacao
    (maior-melhor => esperado negativo contra o nivel => orientado = -rho), com media
    entre as 81 referencias e depois entre os 25 tipos.
    ⭐ Isso tambem fixa uma coisa que nenhuma legenda diz: o alvo e o NIVEL, nao o DMOS.
    """
    por_tipo = {}
    for tipo, g in df.groupby('tipo'):
        rs = []
        for _ref, gg in g.groupby('ref'):
            v = np.array([escores.get(x, np.nan) for x in gg['dist_img']], float)
            ok = np.isfinite(v)
            if ok.sum() < 3:
                continue
            r = spearmanr(v[ok], gg['nivel'].values[ok]).statistic
            if np.isfinite(r):
                rs.append(-r)   # maior-melhor: orientado pela direcao declarada
        if rs:
            por_tipo[int(tipo)] = float(np.mean(rs))
    media = float(np.mean(list(por_tipo.values())))
    return media, sum(1 for v in por_tipo.values() if v > 0.50), por_tipo


def main():
    df = pd.read_csv(H / 'data/kadid10k/kadid10k/dmos.csv')
    df['tipo'] = df['dist_img'].str.split('_').str[1].astype(int)
    df['nivel'] = df['dist_img'].str.split('_').str[2].str.replace('.png', '', regex=False).astype(int)
    df['ref'] = df['dist_img'].str.split('_').str[0]

    cache = json.load(open(H / 'kadid_operacoes.json'))['escores']
    sobel = {k: v['ke_edge_distribution'] for k, v in cache.items()
             if v and 'ke_edge_distribution' in v}
    df = df[df['dist_img'].isin(sobel)].copy()
    assert len(df) > 10000, '⛔ so %d imagens: cache parcial' % len(df)

    m_s, t_s, _ = sensibilidade(sobel, df)
    reproduz = abs(m_s - PUBLICADO['media']) < 0.02 and t_s == PUBLICADO['tipos']
    print('versao SOBEL (a publicada): media %.3f, %d/25 tipos   reproduz o publicado (%.3f, %d): %s'
          % (m_s, t_s, PUBLICADO['media'], PUBLICADO['tipos'], reproduz))
    if not reproduz:
        print('⚠️ o protocolo local nao reproduz o publicado; a comparacao abaixo e '
              'RELATIVA entre as duas versoes, sob o mesmo protocolo.')

    fiel = {}
    for i, nome in enumerate(df['dist_img']):
        img = cv2.imread(str(IMGS / nome))
        if img is None:
            continue
        fiel[nome] = ke_borda_fiel(img)
        if (i + 1) % 2000 == 0:
            print('   %d/%d' % (i + 1, len(df)), flush=True)
    print('  computadas %d imagens com o mapa da fonte' % len(fiel))

    m_f, t_f, _ = sensibilidade(fiel, df)
    comuns = [k for k in fiel if k in sobel]
    rho = spearmanr([sobel[k] for k in comuns], [fiel[k] for k in comuns]).statistic

    out = {
        '_o_que_e': '⛔⛔ A `ke_edge_distribution` refeita com o MAPA LAPLACIANO que a fonte '
                    'especifica, contra a versao com Sobel que produziu os numeros do artigo.',
        'unidade_de_reamostragem': 'imagem do KADID-10k',
        'n_imagens': len(fiel),
        'o_que_a_fonte_especifica': 'Laplaciano 3x3 alpha=0.2, abs, por canal RGB com media '
                                    'entre canais, resize 100x100, soma normalizada a 1 '
                                    '(ke2006highlevel, sec. 4.1)',
        'o_que_o_artigo_rodou': 'magnitude de Sobel sobre o cinza, tamanho nativo, sem normalizar',
        'a_formula_e_a_mesma': '1 - wx*wy, com massa de 98 %',
        'PRE_CONDICAO': {
            'sensibilidade_da_versao_sobel': round(m_s, 4),
            'tipos_acima_de_0_50': t_s,
            'publicado': PUBLICADO,
            'reproduz_o_publicado': bool(reproduz),
        },
        'COM_O_MAPA_DA_FONTE': {
            'sensibilidade': round(m_f, 4),
            'tipos_acima_de_0_50': t_f,
            'delta_na_sensibilidade': round(m_f - m_s, 4),
            'delta_nos_tipos': t_f - t_s,
        },
        'concordancia_entre_as_duas': {
            'spearman_escore_a_escore': round(float(rho), 4),
            'n_pares': len(comuns),
        },
        'O_VEREDITO_DA_PORTA': {
            'limiar': 'media >= 0,50 E >= 15 de 25 tipos',
            'sobel_passa': bool(m_s >= 0.50 and t_s >= 15),
            'fonte_passa': bool(m_f >= 0.50 and t_f >= 15),
            'o_veredito_muda': bool((m_s >= 0.50 and t_s >= 15) != (m_f >= 0.50 and t_f >= 15)),
        },
    }
    out['leitura'] = (
        'Com o mapa da fonte a sensibilidade vai de %.3f para %.3f (%+.3f) e os tipos de '
        '%d para %d. O veredito da porta %s. As duas versoes correlacionam %.3f entre si. '
        '⛔ Seja qual for o delta, a linha nao pode continuar a ser descrita como '
        'reproducao do mapa da fonte: ou se adota este, ou se declara a adaptacao.'
        % (m_s, m_f, m_f - m_s, t_s, t_f,
           'MUDA' if out['O_VEREDITO_DA_PORTA']['o_veredito_muda'] else 'NAO muda', rho))
    json.dump(out, open(H / 'a_borda_do_ke_com_o_mapa_da_fonte.json', 'w'),
              indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
