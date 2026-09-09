#!/usr/bin/env python3
"""A MATRIZ DE COBERTURA: qual operacao entrou em qual teste, e por que nao entrou.

POR QUE EXISTE (07/09/2026). A legenda da Fig. 1 dizia que os quatro testes eram aplicados
«identically to every operation», e o proprio artigo documenta cobertura parcial em varios
pontos. Repetir «protocolo identico» e mais fraco do que mostrar a matriz.

⚠️ E os motivos NAO sao todos do mesmo tipo, o que a tabela precisa distinguir:
  - o `si` nao recebe veredito pareado porque a FONTE nao declara direcao: motivo de principio;
  - sete operacoes nao entram no jusante porque a passada do jusante e ANTERIOR a entrada
    delas no codigo: motivo de historia de implementacao, nao de metodo. Fica dito assim.
"""
import json
from pathlib import Path

QB = Path('/dados/Projetos/quality-benchmark')
SAIDA = Path(__file__).parent / 'tab_cobertura.tex'
NOME = {'ke_edge_distribution': 'Edge distribution', 'qaroush_go': 'Gradient orientation',
        'si': 'Spatial information', 'ke_contraste': 'Contrast',
        'contraste_variancia': 'Contrast variance', 'ke_hue_count': 'Hue count',
        'qaroush_entropia': 'Entropy', 'qaroush_gm': 'Gradient magnitude',
        'qaroush_saliencia': 'Saliency area', 'gygli_media_crua': 'Averaged aesthetics (3)',
        'srinivas_quality': 'Composite of five', 'glcm_contraste': 'GLCM contrast',
        'laplacian_var': 'Laplacian variance', 'huang_saturacao': 'Saturation',
        'hasler_colorfulness': 'Colourfulness (Hasler)',
        'ke_colorfulness': 'Colourfulness (Ke)'}


def main():
    ops = json.load(open(QB / 'as_15_na_regra_do_artigo.json'))['por_operacao']
    res = json.load(open(QB / 'ops_da_literatura_designA.json'))['resumo_designA']
    piso = {x['operacao'] for x in
            json.load(open(QB / 'o_piso_das_operacoes_isoladas_e_estavel.json'))['por_operacao']}
    jus = {x['nome'] for x in json.load(open(QB / 'jusante_lado_a_lado.json'))['linhas']
           if 'sumarizacao' in x['familia']}

    S, N = r'\textcolor{accentgreen!70!black}{\textbf{$\bullet$}}', \
        r'\textcolor{black!28}{$\circ$}'
    linhas, cont = [], {'par': 0, 'sen': 0, 'gen': 0, 'pis': 0, 'jus': 0}
    for k in sorted(ops, key=lambda x: NOME[x]):
        o = ops[k]
        c = {'par': res.get(k, {}).get('direcao_maior_melhor') is not None,
             'sen': o.get('sensibilidade_media') is not None,
             'gen': o.get('menor_rho_em_base_nao_vista') is not None,
             'pis': k in piso, 'jus': k in jus}
        for a, v in c.items():
            cont[a] += v
        nota = ('source declares no direction' if not c['par'] else
                ('after the downstream pass' if not c['jus'] else ''))
        linhas.append((NOME[k], c, nota))

    L = [r'\begin{table}[!ht]', r'\centering',
         r'\caption{Which operation entered which test. A filled marker means the operation '
         r'has a result on that axis. \textbf{Coverage is not uniform, and the two reasons '
         r'differ.} Spatial information carries no paired verdict because its source declares '
         r'no direction, which is a property of the source. The seven operations without a '
         r'downstream result were added to the implementation after the downstream pass was '
         r'run, which is a property of our sequence of work and not of the method; extending '
         r'that pass to them is a stated next step. Sensitivity and generalization cover all '
         rf'{len(linhas)}. Counts per axis are in the last row.' + '}',
         r'\label{tab:coverage}', r'\small', r'\setlength{\tabcolsep}{3pt}',
         r'\renewcommand{\arraystretch}{1.06}',
         r'\begin{tabular}{@{}l ccccc >{\raggedright\arraybackslash}p{3.2cm}@{}}', r'\toprule',
         r'\rowcolor{headerblue}',
         r'\hd{Operation} & \hd{Paired} & \hd{Sens.} & \hd{Gen.} & \hd{Floor} & '
         r'\hd{Down.} & \hd{Absent because} \\', r'\midrule']
    for i, (nome, c, nota) in enumerate(linhas):
        cor = r'\rowcolor{rowlight}' if i % 2 else ''
        m = ' & '.join(S if c[a] else N for a in ('par', 'sen', 'gen', 'pis', 'jus'))
        L.append(f"{cor}{nome} & {m} & \\textcolor{{black!55}}{{\\scriptsize {nota}}} \\\\")
    L += [r'\midrule',
          r'\textbf{of ' + str(len(linhas)) + r'} & ' +
          ' & '.join(f"\\textbf{{{cont[a]}}}" for a in ('par', 'sen', 'gen', 'pis', 'jus')) +
          r' & \\', r'\bottomrule', r'\end{tabular}', r'\end{table}']
    SAIDA.write_text('\n'.join(L) + '\n')
    print(f'  {len(linhas)} operacoes x 5 testes -> {SAIDA.name}')
    print(f'  cobertura: {cont}')


if __name__ == '__main__':
    main()
