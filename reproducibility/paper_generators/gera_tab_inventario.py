#!/usr/bin/env python3
"""Tabela 1: o inventario. Cada operacao ligada ao objetivo do trabalho de origem, ao
papel que ela tem la, e a leitura que este artigo testa. Existe para separar
«falha no objetivo declarado» de «nao se reusa como medida de qualidade sem validacao»."""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_inventario.tex'

# objetivo declarado NA FONTE, e papel que a operacao tem la. Conferido nos PDFs.
FONTE = {
 'ke_edge_distribution':  ('ke2006highlevel', 'Professional vs.\\ snapshot photograph', 'feature of a naive Bayes classifier'),
 'ke_contraste':          ('ke2006highlevel', 'Professional vs.\\ snapshot photograph', 'feature of a naive Bayes classifier'),
 'ke_hue_count':          ('ke2006highlevel', 'Professional vs.\\ snapshot photograph', 'feature of a naive Bayes classifier'),
 'ke_colorfulness':       ('ke2006highlevel', 'Professional vs.\\ snapshot photograph', 'feature of a naive Bayes classifier'),
 'hasler_colorfulness':   ('hasler2003colorfulness', 'Perceived colourfulness of a scene', 'stand-alone perceptual index'),
 'srinivas_quality':      ('srinivas2016rank', 'Keyframe ranking', 'unweighted mean of five features'),
 'gygli_media_crua':      ('gygli2014summe', 'Keyframe interestingness', 'unweighted mean of three aesthetic terms; the source gives no weights'),
 'qaroush_go':              ('qaroush2025diversity', 'Keyframe diversity and coverage', 'GO in segment diversity (Eq.~22)'),
 'qaroush_gm':              ('qaroush2025diversity', 'Keyframe diversity and coverage', 'GM in visual attention (Eq.~20)'),
 'qaroush_entropia':        ('qaroush2025diversity', 'Keyframe diversity and coverage', 'SE in segment coverage (Eq.~21)'),
 'qaroush_saliencia':       ('qaroush2025diversity', 'Keyframe diversity and coverage', 'VS in visual attention (Eq.~20)'),
 'glcm_contraste':        ('yang2024keyframe', 'Keyframe extraction', 'texture descriptor'),
 'laplacian_var':         ('cakmak2025tripss', 'Blur rejection in frame filtering', 'sharpness threshold'),
 'contraste_variancia':   ('jeong2016static', 'Static-frame selection',
                          'one of four inputs to a cost multiplicative in cluster distance'),
 'huang_saturacao':       ('huang2024aesthetic', 'Aesthetic scoring', 'one term among several'),
 'si':                    ('itu_p910', 'Spatial detail of a test sequence', 'characterization, not quality'),
}
NOME = {'ke_edge_distribution':'Edge distribution','qaroush_go':'Gradient orientation',
 'si':'Spatial information','ke_contraste':'Contrast','contraste_variancia':'Contrast variance',
 'ke_hue_count':'Hue count','qaroush_entropia':'Entropy','qaroush_gm':'Gradient magnitude',
 'qaroush_saliencia':'Saliency area','gygli_media_crua':'Averaged aesthetics (3)',
 'srinivas_quality':'Composite of five','glcm_contraste':'GLCM contrast',
 'laplacian_var':'Laplacian variance','huang_saturacao':'Saturation',
 'hasler_colorfulness':'Colourfulness (Hasler)','ke_colorfulness':'Colourfulness (Ke)'}


def main():
    A16 = json.load(open(QB / 'proveniencia_das_operacoes.json'))['as_16_da_tabela_de_triagem']
    des = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
    L = [r'\begin{table}[!ht]', r'\centering',
         r'\caption{The sixteen operations audited, each linked to the objective its '
         r'source states and the role it has there. \emph{Tested reading} is the one this '
         r'article evaluates: higher score means better technical quality, applied '
         r'to a single frame without a model. No source is claimed to be wrong about its '
         r'own objective; what is tested is the reuse. \emph{Inverts} counts degradation '
         r'types on which the operation ranks the degraded copy higher '
         # ⚠️ esta tabela vive no SUPLEMENTAR; `\ref` nao alcanca a figura do corpo
         r'(Fig.~2 of the main article). Where two works adopt the same operation the use can '
         r'differ: Laplacian variance rejects low-light frames alongside grey-scale intensity '
         # ⛔ AQUI havia `\\citet` DENTRO de raw string, o que emite `\\citet` no .tex:
         # o LaTeX leu `\\` como quebra de linha e `citet{...}` como TEXTO. A legenda saiu
         # com «citetcakmak2025tripss» e com o math vazando, e compilou sem erro nenhum.
         # Em raw string a barra e UMA so.
         r'and a Canny detector in \citet{cakmak2025tripss}, and enters '
         r'$0.7\,z(\mathrm{sharp})+0.3\,z(\mathrm{bright})$ in \citet{korolkov2025keyframe}.}',
         r'\label{tab:inventory}', r'\footnotesize', r'\setlength{\tabcolsep}{4pt}',
         r'\renewcommand{\arraystretch}{1.15}',
         r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.45cm}'
         r'>{\raggedright\arraybackslash}p{3.5cm}'
         r'>{\raggedright\arraybackslash}p{3.4cm}c@{}}', r'\toprule',
         r'\rowcolor{headerblue}',
         r'\hd{Operation} & \hd{Objective in the source} & \hd{Role there} & '
         r'\hd{Inverts} \\', r'\midrule']
    for i, k in enumerate(sorted(A16, key=lambda o: NOME.get(o, o))):
        cite, obj, papel = FONTE[k]
        v = des.get(k, {})
        a = v.get('acuracia_por_tipo') or []
        n = sum(1 for x in a if x is not None and x < 50) if a and all(
            x is not None for x in a) else None
        marca = (r'\textcolor{accentred}{\textbf{%d}/8}' % n) if n else (
            r'\textcolor{black!45}{---}' if n is None else '0/8')
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        L.append(f"{cor}{NOME.get(k,k)}~\\citep{{{cite}}} & {obj} & {papel} & {marca} \\\\")
    L += [r'\midrule',
          r'\multicolumn{4}{@{}p{0.95\linewidth}}{\footnotesize \emph{Tested reading, '
          r'identical for all sixteen}: the operation is computed on one frame and read '
          r'as a technical-quality score in which a higher value marks the better of two '
          r'versions of the same content. Fifteen are closed-form; saliency area requires '
          r'a learned map in its source and is marked as such.} \\',
          r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(A16)} linhas -> {SAIDA.name}')


if __name__ == '__main__':
    main()
