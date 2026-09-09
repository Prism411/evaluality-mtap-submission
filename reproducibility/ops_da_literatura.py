"""As operacoes de qualidade visual que a literatura de sumarizacao de fato usa.

Cada funcao implementa o NUCLEO MINIMO de uma operacao lida NA FONTE, com a
referencia e a ressalva de interpretacao ao lado. Nao implementa a arquitetura
que a embala: implementa o que calcula o numero, que e a regra de extracao do
Jader (02/09): "as vezes ele usou o transformer mas na verdade so usou histograma
de cor RGB; no nosso caso implementariamos o histograma".

Convencao: TODAS devolvem "maior = melhor" quando o trabalho de origem trata o
atributo como desejavel; onde o sinal e ambiguo, esta declarado no docstring.
"""
import numpy as np
import cv2


# ---------------------------------------------------------------- Hasler 2003
def hasler_colorfulness(bgr):
    """M(3) = sigma_rgyb + 0.3*mu_rgyb   (Hasler & Suesstrunk, SPIE 5007, sec.7)

    rg = R-G ; yb = (R+G)/2 - B ; sigma_rgyb = sqrt(s_rg^2+s_yb^2) ; idem mu.
    ⭐ E a UNICA do menu validada por psicofisica: correlacao 95,3 % com o
    experimento de escalonamento por categorias. Tabela 2 do artigo da a escala:
    0 nao colorido, 15 pouco, 33 moderado, 45 medio, 59 bastante, 82 muito,
    109 extremamente.
    """
    b, g, r = (x.astype(np.float64) for x in cv2.split(bgr))
    rg = r - g
    yb = 0.5 * (r + g) - b
    return float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))


# --------------------------------------- TriPSS 2025 / Korolkov 2025 / Xu 2024
def laplacian_var(bgr):
    """Variancia do Laplaciano em escala de cinza: a medida classica de nitidez.

    Fonte: cakmak2025tripss (sec.3.6, "Laplacian variance"), korolkov2025keyframe
    (Sharpness), e xu2024property usa o operador de Laplace para "edge
    distribution". Maior = mais nitido.
    """
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


# -------------------------------------------------------------- Nandini 2022
def sobel_magnitude(bgr):
    """Magnitude do gradiente Sobel por pixel (insumo do CV do Nandini)."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    gx = cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=3)
    return np.sqrt(gx ** 2 + gy ** 2)


def sobel_cv_da_sequencia(frames, pool=None):
    """CV = sigma/mu da magnitude Sobel Z-scorada (nandini2022edgelbp, Eq.7).

    ⚠️ DUAS INTERPRETACOES DECLARADAS, e as duas foram forcadas pelo artigo:

    (1) O artigo Z-scora as magnitudes e depois toma sigma/mu. Z-score POR
        QUADRO daria mu=0 e CV indefinido, entao o Z-score tem de ser sobre a
        SEQUENCIA (o shot). E o unico jeito de a Eq.7 fechar.
    (2) Para o teste PAREADO (orig contra degradado) o Z-score usa o pool das
        DUAS condicoes (`pool`), senao cada lado seria normalizado pelo proprio
        desvio e a comparacao mediria a normalizacao, nao a operacao.

    🔴 FRAGILIDADE MEDIDA, e ela e da operacao, nao da implementacao: com quadros
    muito parecidos a media Z-scorada tende a zero e o CV explode (num teste com
    3 copias do mesmo quadro deu 2,5e16). Guardado com um piso no denominador, e
    o caso e reportado.

    Escolhe o quadro de MAIOR CV: "prominent in the edge region".
    Devolve um CV por quadro.
    """
    mags = [sobel_magnitude(f) for f in frames]
    base = mags if pool is None else [sobel_magnitude(f) for f in pool]
    todos = np.concatenate([m.ravel() for m in base])
    mu, sd = todos.mean(), todos.std()
    if sd == 0:
        return [float("nan")] * len(mags)
    out = []
    for m in mags:
        zi = (m - mu) / sd
        d = zi.mean()
        out.append(float(zi.std() / d) if abs(d) > 1e-6 else float("nan"))
    return out


# ---------------------------------------------------------------- Huang 2024
def huang_saturacao(bgr):
    """f1: media do canal S do HSV (huang2024aesthetic, sec.III-A-1)."""
    return float(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[..., 1].mean())


def huang_matiz(bgr):
    """f2: media do canal H do HSV. ⚠️ Matiz e CIRCULAR: a media aritmetica nao
    e definida. O artigo diz "mean hue" e nao qualifica; implementado como o
    artigo diz, e a ressalva vai declarada."""
    return float(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[..., 0].mean())


def huang_exposicao(bgr):
    """f3: "average pixel intensity" (huang2024aesthetic). Maior = mais claro,
    e o artigo trata os DOIS extremos como ruins, entao o sinal e ambiguo."""
    return float(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).mean())


# ------------------------------------------- Jeong 2017 / Xu 2024 / Ke 2006
def contraste_variancia(bgr):
    """Contraste como VARIANCIA DE PIXELS.

    jeong2017static: "we measure the contrast as variance of pixels".
    xu2024property: "contrast is calculated by the mean difference and standard
    deviation of the grayscale values". Implementado como o desvio-padrao do
    cinza, que e a leitura comum aos dois. Maior = mais contraste.
    """
    return float(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).std())


def brilho(bgr):
    """Brightness da bateria de Ke/Srinivas: media do cinza. Sinal ambiguo."""
    return float(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).mean())


# ----------------------------------------------------------------- registro
POR_QUADRO = {
    "hasler_colorfulness": hasler_colorfulness,
    "laplacian_var": laplacian_var,
    "huang_saturacao": huang_saturacao,
    "huang_matiz": huang_matiz,
    "huang_exposicao": huang_exposicao,
    "contraste_variancia": contraste_variancia,
    "brilho": brilho,
}
POR_SEQUENCIA = {"sobel_cv": sobel_cv_da_sequencia}

# maior = melhor? None quando o proprio trabalho de origem nao define direcao
DIRECAO = {
    "hasler_colorfulness": True, "laplacian_var": True,
    "contraste_variancia": True, "sobel_cv": True,
    "huang_saturacao": True, "brilho": None,
    "huang_matiz": None, "huang_exposicao": None,
}


# =========================================================== BATERIA DE Ke 2006
# As cinco features, cada uma conferida na fonte (ke2006highlevel.pdf), mais o
# COMPOSTO do srinivas2016rank, que e a media simples das cinco.

def ke_edge_distribution(bgr):
    """q_a = 1 - wx*wy   (Ke, sec.4.1)

    Projeta o mapa de bordas nos dois eixos, mede a LARGURA DA MASSA DE 98 % de
    cada projecao, e o escore e 1 menos a area da caixa. Alto = bordas
    concentradas = "simples" = melhor, no criterio do Ke.
    """
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    gx = cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=3)
    L = np.sqrt(gx ** 2 + gy ** 2)
    def largura98(proj):
        t = proj.sum()
        if t <= 0:
            return 1.0
        c = np.cumsum(proj) / t
        lo = int(np.searchsorted(c, 0.01))
        hi = int(np.searchsorted(c, 0.99))
        return max(hi - lo, 1) / len(proj)
    wx = largura98(L.sum(axis=0))   # projecao em x
    wy = largura98(L.sum(axis=1))   # projecao em y
    return float(1.0 - wx * wy)


def ke_hue_count(bgr):
    """q_h = 20 - |N|   (Ke, sec.4.3, com alpha = 0.05)

    Histograma de 20 bins do matiz, so em pixels com V em [0.15,0.95] e S > 0.2;
    N sao os bins acima de 0.05*max. Alto = POUCOS matizes = "simplicidade" =
    melhor, no criterio do Ke. Imagem em cinza tem hue count 1, logo q_h = 19.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0].astype(np.float64), hsv[..., 1] / 255.0, hsv[..., 2] / 255.0
    bons = h[(v >= 0.15) & (v <= 0.95) & (s > 0.2)]
    if bons.size == 0:
        return 19.0                      # equivale ao caso "grayscale", contagem 1
    H, _ = np.histogram(bons, bins=20, range=(0, 180))
    m = H.max()
    if m == 0:
        return 19.0
    return float(20 - int((H > 0.05 * m).sum()))


def ke_contraste(bgr):
    """Largura da massa dos 98 % centrais do histograma de cinza (Ke, sec.4.5 e
    Fig.6). Maior largura = mais contraste = melhor, no criterio do Ke.
    ⚠️ NAO e o desvio-padrao: e a largura do intervalo central de 98 % da massa.
    """
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    H = np.bincount(g.ravel(), minlength=256).astype(np.float64)
    t = H.sum()
    if t <= 0:
        return 0.0
    c = np.cumsum(H) / t
    lo = int(np.searchsorted(c, 0.01))
    hi = int(np.searchsorted(c, 0.99))
    return float(max(hi - lo, 0))


KE_CINCO = {
    "ke_colorfulness": hasler_colorfulness,   # ⚠️ Ke nao define; Hasler e o padrao declarado
    "ke_brightness": brilho,
    "ke_edge_distribution": ke_edge_distribution,
    "ke_hue_count": ke_hue_count,
    "ke_contraste": ke_contraste,
}


def srinivas_quality(bgr):
    """O escore Quality do srinivas2016rank: MEDIA SIMPLES das cinco do Ke.

    Verbatim: "The AVERAGE of all these individual scores for each frame is its
    Quality score." ⚠️ SEM normalizacao declarada — e as cinco vivem em escalas
    diferentes (q_a em [0,1], q_h em [0,20], contraste em [0,255], brilho em
    [0,255], colorfulness em [0,~150]). A media crua e portanto DOMINADA pelos
    termos de maior escala, e isso e medido ao lado, nao suposto.
    """
    return float(np.mean([f(bgr) for f in KE_CINCO.values()]))


POR_QUADRO.update(KE_CINCO)
POR_QUADRO["srinivas_quality"] = srinivas_quality
DIRECAO.update({"ke_colorfulness": True, "ke_brightness": None,
                "ke_edge_distribution": True, "ke_hue_count": True,
                "ke_contraste": True, "srinivas_quality": True})


# ========================================================== QAROUSH et al. 2025
# Os QUATRO atributos de importancia de segmento (IPM 62:104276, sec. do escore).
# ⚠️ O Qaroush declara SALIENCIA e COMPLEXIDADE, nao qualidade: entra na auditoria
# com o construto declarado dele, e isso vai dito no artigo.

def qaroush_ses(frames):
    """SES, segment size: "quantitatively determined by the NUMBER OF FRAMES".
    Operacao de SEQUENCIA. Maior = mais cobertura temporal, no criterio deles."""
    return float(len(frames))


def qaroush_entropia(bgr):
    """SE, Eq.5: entropia de Shannon sobre os bins do HISTOGRAMA HSV do quadro.

    Verbatim: "the HSV color histogram of each frame is constructed... the entropy
    of each frame is calculated by quantifying the uncertainty associated with the
    pixel distribution within the histogram bins". Media sobre os quadros e feita
    fora. Maior = mais "rico", no criterio deles.
    ⚠️ O numero de bins nao e declarado no artigo. Uso 8x8x8 = 512, e a escolha
    fica DECLARADA aqui, nao escondida.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256]).ravel()
    p = h / h.sum() if h.sum() > 0 else h
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def _saliencia_residuo_espectral(bgr):
    """Mapa de saliencia por RESIDUO ESPECTRAL (Hou & Zhang, CVPR 2007).

    ⚠️ SUBSTITUICAO DECLARADA: o Qaroush usa DenseNet no pre-processamento e uma
    ResNet50 pre-treinada para produzir o mapa. O NUCLEO da operacao dele nao e o
    fundo profundo: e "a thresholding operation is applied to the saliency map...
    the resulting salient area is expressed as a PERCENTAGE OF THE TOTAL FRAME
    AREA". O fundo e substituivel; a operacao e a fracao de area. Trocar um mapa
    profundo por um classico muda a MAGNITUDE e nao a natureza da operacao, e essa
    e a diferenca que o artigo tem de declarar.
    """
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.resize(g, (64, 64))
    f = np.fft.fft2(g)
    log_amp = np.log(np.abs(f) + 1e-8)
    fase = np.angle(f)
    media = cv2.blur(log_amp, (3, 3))
    residuo = log_amp - media
    sal = np.abs(np.fft.ifft2(np.exp(residuo + 1j * fase))) ** 2
    sal = cv2.GaussianBlur(sal, (9, 9), 2.5)
    return sal


def qaroush_saliencia(bgr):
    """VS, Eq.6: fracao da area do quadro com saliencia acima de um limiar.

    ⚠️ O limiar `s_tau` NUNCA recebe valor no artigo — e o unico parametro sem
    numero, enquanto o tau da segmentacao vale 65, o damping do PageRank 0,85 e o
    alpha do motion 0,4. Uso a MEDIA do proprio mapa, que e a escolha sem
    parametro livre, e ela fica declarada.
    """
    s = _saliencia_residuo_espectral(bgr)
    return float(100.0 * (s >= s.mean()).mean())


def qaroush_movimento(frames, alpha=0.4):
    """MS = alpha*MMI + (1-alpha)*MD, Eq. 7-9, com alpha = 0.4.

    MMI: media da magnitude do fluxo optico entre quadros consecutivos.
    MD : desvio-padrao dessas intensidades ao longo do segmento.
    ⚠️ alpha = 0,4 e verbatim do artigo ("set to 0.4 in this study"), SEM
    justificativa e SEM varredura, e isso e parte do achado.
    Operacao de SEQUENCIA.
    """
    if len(frames) < 2:
        return 0.0
    ints = []
    prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    for f in frames[1:]:
        cur = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        fl = cv2.calcOpticalFlowFarneback(prev, cur, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        ints.append(float(np.mean(np.sqrt(fl[..., 0] ** 2 + fl[..., 1] ** 2))))
        prev = cur
    return float(alpha * np.mean(ints) + (1 - alpha) * np.std(ints))


# ============================================================ TEXTURA (pedido do Jader)
# LBP aparece em zhang2015aesthetics e zhang2016georeferenced; GLCM em yang2024keyframe.

def lbp_uniformidade(bgr, P=8, R=1):
    """Fracao de padroes LBP UNIFORMES (Ojala/Pietikainen), o descritor de textura
    que o zhang2015aesthetics e o zhang2016georeferenced usam como feature.
    Textura regular -> mais padroes uniformes. Maior = mais "regular"."""
    from skimage.feature import local_binary_pattern
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(g, P, R, method="uniform")
    return float((lbp < P + 1).mean())


def glcm_contraste(bgr, d=1):
    """Contraste da matriz de co-ocorrencia de niveis de cinza (GLCM), o descritor
    que o yang2024keyframe usa. Media sobre as 4 direcoes."""
    from skimage.feature import graycomatrix, graycoprops
    g = (cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) // 8).astype(np.uint8)   # 32 niveis
    m = graycomatrix(g, [d], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32, symmetric=True, normed=True)
    return float(graycoprops(m, "contrast").mean())


def glcm_homogeneidade(bgr, d=1):
    """Homogeneidade da GLCM: alta quando a textura e suave."""
    from skimage.feature import graycomatrix, graycoprops
    g = (cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) // 8).astype(np.uint8)
    m = graycomatrix(g, [d], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32, symmetric=True, normed=True)
    return float(graycoprops(m, "homogeneity").mean())


# ============================================================ COMPOSTO DO GYGLI
def gygli_aesthetics(bgr):
    """A parte "Aesthetics/Quality" do interestingness do gygli2014creating.

    Verbatim, e sao TRES linhas: "To predict the aesthetic quality of a frame we
    compute COLORFULNESS [Datta], CONTRAST [Ke] and the DISTRIBUTION OF EDGES [Ke]."
    ⚠️ Ele nao diz COMO combina os tres no escore de interestingness (e uma "weighted
    sum of features" cujos pesos nao aparecem). Uso media dos tres apos min-max
    global, e a escolha fica declarada: SEM normalizar, o contraste (0-255) domina
    os outros dois, que e exatamente o defeito medido no composto do Srinivas.
    Aqui a media crua tambem e reportada, para os dois se compararem.
    """
    return (hasler_colorfulness(bgr), ke_contraste(bgr), ke_edge_distribution(bgr))


POR_QUADRO.update({
    "qaroush_entropia": qaroush_entropia,
    "qaroush_saliencia": qaroush_saliencia,
    "lbp_uniformidade": lbp_uniformidade,
    "glcm_contraste": glcm_contraste,
    "glcm_homogeneidade": glcm_homogeneidade,
})
POR_SEQUENCIA.update({"qaroush_ses": qaroush_ses, "qaroush_movimento": qaroush_movimento})
DIRECAO.update({
    "qaroush_entropia": True,      # "high entropy exhibits a broad spectrum of visual content"
    "qaroush_saliencia": True,     # mais area saliente = mais proeminente
    "qaroush_ses": True,           # segmento maior = mais cobertura
    "qaroush_movimento": True,     # "crucial for generating engaging summaries"
    "lbp_uniformidade": None,      # o trabalho de origem nao declara direcao
    "glcm_contraste": True,        # contraste maior = mais textura
    "glcm_homogeneidade": None,    # direcao nao declarada
})


def gygli_media_crua(bgr):
    """O composto do Gygli como MEDIA CRUA dos tres, para ser o par direto do
    srinivas_quality: os dois somam features de escalas incompativeis sem
    normalizar, e a comparacao mostra se o defeito e do conjunto ou da soma."""
    return float(np.mean(gygli_aesthetics(bgr)))


POR_QUADRO["gygli_media_crua"] = gygli_media_crua
DIRECAO["gygli_media_crua"] = True

# ⭐ CONTRASTE QUE VALE O ARTIGO: o Qaroush NORMALIZA antes de somar e o Srinivas
# NAO. Verbatim do Qaroush: "each is normalized using Min-Max scaling... we
# guarantee that all features contribute equally to the SSC calculation". O
# composto SSC = SES + SE + VS + MS (Eq.10) e montado na analise, onde as
# estatisticas globais existem; aqui ficam os quatro termos separados.
QAROUSH_QUATRO = ["qaroush_ses", "qaroush_entropia", "qaroush_saliencia", "qaroush_movimento"]
KE_CINCO_NOMES = list(KE_CINCO)
GYGLI_TRES = ["hasler_colorfulness", "ke_contraste", "ke_edge_distribution"]


# ====================================================== QAROUSH GM e GO (03/09)
# Duas operacoes POR QUADRO do qaroush2025diversity que faltavam no inventario.
# Levantadas conferindo o artigo na fonte, nao pela varredura por termo.
# ⚠️ As equacoes foram lidas com `pdftotext -layout`. SEM o -layout a extracao
# intercala as duas colunas e devolve para a Eq.15 a formula `sigma_p(gray(f_k))`,
# que e desvio do CINZA e nao da ORIENTACAO. Implementar dali daria uma operacao
# errada com valor plausivel.

def qaroush_gm(bgr):
    """GM, Eq.10: media da magnitude do gradiente Sobel do quadro em cinza.

    `GM(s) = (1/K) sum_k mu_p(SGM(gray(f_k)))`, e como a media sobre quadros e
    feita pelo arcabouco, aqui fica so o `mu_p` de um quadro.
    ⭐ DISTINTA do `sobel_cv`, que e sigma/mu sobre a sequencia Z-scorada: esta e
    a media crua por quadro. Maior = bordas mais proeminentes.
    """
    return float(np.mean(sobel_magnitude(bgr)))


def qaroush_go(bgr):
    """GO, Eq.15: desvio-padrao das ORIENTACOES do gradiente Sobel.

    `GO(s) = (1/K) sum_k sigma_p(SGO(gray(f_k)))`. Maior = mais diversidade de
    direcao de borda, que o artigo le como riqueza textural.

    ⚠️ ARTEFATO DECLARADO, e ele e do artigo, nao da implementacao: orientacao e
    grandeza CIRCULAR (0 e 2*pi sao o mesmo angulo) e o artigo aplica desvio
    LINEAR. Uma imagem com bordas em torno de 0 grau tem orientacoes espalhadas
    entre ~0 e ~2*pi e recebe desvio ALTO, quando a dispersao circular e BAIXA.
    Implementado como o artigo especifica, com a alternativa circular ao lado
    para quem quiser medir a diferenca.
    """
    g = sobel_magnitude(bgr)  # so para reaproveitar a conversao
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    ang = np.arctan2(gy, gx)                      # -pi a pi
    return float(np.std(ang))


def qaroush_go_circular(bgr):
    """A MESMA Eq.15 com desvio CIRCULAR, que e o estatisticamente correto.

    Existe para MEDIR o custo do artefato de `qaroush_go`, nao para substituir a
    operacao do artigo. Desvio circular = sqrt(-2*ln(R)), R = |media dos vetores
    unitarios|. Nao entra nas tabelas da literatura: entra na tabela de artefatos.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    ang = np.arctan2(gy, gx)
    R = np.hypot(np.mean(np.cos(ang)), np.mean(np.sin(ang)))
    R = min(max(float(R), 1e-12), 1.0)
    return float(np.sqrt(-2.0 * np.log(R)))


def qaroush_ct(bgr):
    """CT, Eq. 8: |sigma_p(HE(gray(f))) - sigma_p(gray(f))|.

    Verbatim: "We compute contrast by comparing the standard deviation of pixel
    intensities BEFORE and AFTER histogram equalization"; `sigma_p` e o desvio sobre
    PIXELS, a mesma notacao que a Eq. 8 usa. Maior = mais contraste, no criterio deles.

    ⚠️ NAO e a `contraste_variancia` (variancia de pixel, do jeong2016static) nem a
    `ke_contraste` (largura dos 98 % centrais do histograma). E um TERCEIRO construto
    chamado "contraste", e o VAScore do Qaroush pede este.
    """
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return float(abs(float(cv2.equalizeHist(g).std()) - float(g.std())))


def qaroush_mmi(frames):
    """MMI puro: media, sobre os pares consecutivos, de mu_p(opticalFlow(f_k, f_k+1)).

    ⚠️ NAO e a `qaroush_movimento`, que e o MS = 0,4*MMI + 0,6*MD. O VAScore (Eq. 20)
    pede MMI SOZINHO; o MD entra no SDScore (Eq. 22), que e outro objetivo.
    Operacao de SEQUENCIA.
    """
    if len(frames) < 2:
        return 0.0
    ints = []
    prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    for f in frames[1:]:
        cur = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        fl = cv2.calcOpticalFlowFarneback(prev, cur, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        ints.append(float(np.mean(np.sqrt(fl[..., 0] ** 2 + fl[..., 1] ** 2))))
        prev = cur
    return float(np.mean(ints))


def korolkov_brilho(bgr):
    """Brightness do korolkov2025keyframe: media do canal L em LAB.

    Verbatim: «Brightness: Average luminance in the LAB color space ... Penalizes under-
    and over-exposed frames.»
    ⚠️ NAO e a `brilho` (media do cinza, da bateria de Ke). O modulo do Korolkov pede esta.
    """
    return float(cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[..., 0].mean())


POR_QUADRO.update({"qaroush_gm": qaroush_gm, "qaroush_go": qaroush_go,
                   "qaroush_ct": qaroush_ct, "korolkov_brilho": korolkov_brilho})
DIRECAO["korolkov_brilho"] = None

# ⭐ O modulo COMPLETO do Korolkov, secao 4.4: z-score dos dois termos e soma ponderada,
# com w_sharp = 0,7 e w_bright = 0,3 verbatim, e argmax do resultado.
KOROLKOV_MODULO = {"laplacian_var": 0.7, "korolkov_brilho": 0.3}
POR_SEQUENCIA.update({"qaroush_mmi": qaroush_mmi})
DIRECAO.update({"qaroush_ct": True, "qaroush_mmi": None})

# ⭐ O VAScore do Qaroush, Eq. 20: soma NAO ponderada dos cinco termos de atencao visual.
# CF vem do Hasler (a fonte diz "building upon Hasler and Susstrunk (2003)").
QAROUSH_VASCORE = ["hasler_colorfulness", "qaroush_ct", "qaroush_saliencia",
                   "qaroush_gm", "qaroush_mmi"]
DIRECAO.update({"qaroush_gm": True, "qaroush_go": True})
