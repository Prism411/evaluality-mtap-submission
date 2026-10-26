#!/usr/bin/env python3
"""⛔ Celula abaixo do piso de acaso que a Tabela 3 nao marca.

⭐ TRAZIDA PARA DENTRO DO PACOTE em 12/09/2026. Ela vivia em `agent/ferramentas/` do vault
apontando para o pacote ANTIGO (`earlier-workspace/venue/`), junto com outras onze.
Repontada para o pacote que vai ser submetido, ela ACHOU NA HORA a mesma celula outra vez:
o 47 do HyperIQA sob escurecimento tinha marca no pacote antigo e a PERDEU na migracao.
⚠️ Uma guarda que le o documento errado nao e guarda: ela dizia ✅ sobre um artigo que
ninguem vai submeter. Aqui ela le o `sec_results.tex` ao lado dela, e entra na suite.

POR QUE EXISTE (06/09). A legenda declara que valor abaixo de 50 % e inversao
sistematica, e a tabela marca essas celulas em vermelho e negrito. ⚠️ Uma escapou: o
47 do HyperIQA sob escurecimento ficou sem marca, e a familia dos modelos parecia mais
limpa do que e. Achado por um revisor, nao por mim.

⭐ O teste e a propria regra da legenda: TODA celula numerica abaixo de 50 tem de estar
marcada, e nenhuma acima. Um valor de cor no `\\rowcolor{focoauditado!12}` nao e celula: a
leitura ignora tudo que vem antes do primeiro `&`.
"""
import re, sys
from pathlib import Path

ART = Path(__file__).parent / "sec_results.tex"
MARCA = r'\textcolor{accentred}{\textbf{'


def linhas_da_tabela(texto):
    i = texto.find('unmodified--degraded broadcast pairs')
    if i < 0: return []
    j = texto.find(r'\end{tabular}', i)
    return [l for l in texto[i:j].split('\n')
            if '&' in l and 'hd{' not in l and not l.strip().startswith('%')]


def fora_da_regra(texto):
    ruins = []
    for l in linhas_da_tabela(texto):
        metodo, _, resto = l.partition('&')      # ⭐ o rowcolor fica fora
        for cel in resto.split('&'):
            m = re.search(r'(\d+(?:\.\d+)?)', cel)
            if not m: continue
            v = float(m.group(1))
            marcada = MARCA in cel
            if v < 50 and not marcada:
                ruins.append((metodo.strip()[-24:], v, 'abaixo de 50 e SEM marca'))
            elif v >= 50 and marcada:
                ruins.append((metodo.strip()[-24:], v, 'marcada e NAO esta abaixo de 50'))
    return ruins


def main():
    if not ART.exists():
        print('  ⏳ sec_results.tex nao encontrado'); return 0
    r = fora_da_regra(ART.read_text(encoding='utf-8', errors='replace'))
    if r:
        print(f'  ⛔ {len(r)} celula(s) fora da regra declarada na legenda da Tabela 3:')
        for met, v, por in r: print(f'       {met}: {v} — {por}')
        return 1
    print('  ✅ toda celula abaixo de 50 na Tabela 3 esta marcada, e so essas')
    return 0


def autoteste():
    bom = ('unmodified--degraded broadcast pairs\n'
           'A & 100 & \\textcolor{accentred}{\\textbf{30}} \\\\\n\\end{tabular}')
    mau = ('unmodified--degraded broadcast pairs\n'
           'HyperIQA & 47 & \\textcolor{accentred}{\\textbf{30}} \\\\\n\\end{tabular}')
    casos = [(bom, 0, 'tabela em regra'), (mau, 1, 'o caso real do 47 sem marca')]
    mal = 0
    for txt, esperado, nome in casos:
        n = len(fora_da_regra(txt))
        ok = n == esperado
        mal += not ok
        print(f"  {'✅' if ok else '⛔'} {nome}: achou {n}, esperado {esperado}")
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(autoteste() if '--autoteste' in sys.argv else main())
