#!/usr/bin/env python3
"""⛔ POR QUE O SURF NAO ENTRA NA ABLACAO DE DESCRITORES, E ISSO E VERIFICAVEL?

POR QUE EXISTE (22/09/2026, parecer M12). O artigo dizia que um descritor ficou de fora
«for lack of a redistributable implementation», sem NOMEAR qual nem dizer sob que condicao.
⛔ E eu tinha registrado a resposta em 21/09 e mesmo assim marquei o item como pendencia do
autor. Nao era: e um fato do ambiente, e se confere rodando.

⭐ O QUE ESTE SCRIPT ESTABELECE, na maquina em que as medicoes rodaram:
  - a versao do OpenCV instalado;
  - que `cv2.xfeatures2d` NAO existe nela, que e onde o SURF mora;
  - que os quatro descritores da ablacao (SIFT, ORB, AKAZE, BRISK) existem.

⚠️ A condicao de licenca e a razao de o modulo nao vir no pacote: o SURF e patenteado e
so e compilado em build nao-livre, com `OPENCV_ENABLE_NONFREE=ON`. **Isso e propriedade da
distribuicao de referencia, nao recorte nosso**, e e assim que vai declarado.
"""
import json
from pathlib import Path

SAIDA = Path(__file__).resolve().parent / 'o_surf_esta_fora_por_licenca.json'


def main():
    import cv2
    tem = {n: hasattr(cv2, n) for n in
           ('SIFT_create', 'ORB_create', 'AKAZE_create', 'BRISK_create')}
    try:
        cv2.xfeatures2d.SURF_create()
        surf, erro = True, None
    except Exception as e:
        surf, erro = False, '%s: %s' % (type(e).__name__, e)
    r = {'_o_que_e': __doc__,
         'opencv': cv2.__version__,
         'xfeatures2d_presente': hasattr(cv2, 'xfeatures2d'),
         'surf_instanciavel': surf,
         'erro_ao_instanciar': erro,
         'descritores_da_ablacao_presentes': tem,
         'condicao_declarada': ('patenteado; distribuido apenas em build nao-livre '
                                'compilada da fonte com OPENCV_ENABLE_NONFREE=ON'),
         'previsoes': {}}
    # ⛔ o controle: se o SURF passar a existir, a frase do artigo fica falsa e isto quebra.
    r['previsoes']['1_o_surf_continua_indisponivel'] = (
        'CONFIRMADA' if not surf else '⛔ FALHOU: o SURF existe nesta instalacao')
    r['previsoes']['2_os_quatro_da_ablacao_existem'] = (
        'CONFIRMADA' if all(tem.values()) else '⛔ FALHOU: %s' % tem)
    SAIDA.write_text(json.dumps(r, indent=1, ensure_ascii=False))
    for k, v in r['previsoes'].items():
        print(f"  {'✅' if v == 'CONFIRMADA' else '⛔'} {k}: {v}")
    print(f"  OpenCV {r['opencv']} | xfeatures2d: {r['xfeatures2d_presente']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
