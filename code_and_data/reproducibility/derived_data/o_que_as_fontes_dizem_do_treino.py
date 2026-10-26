#!/usr/bin/env python3
"""⭐⭐ A COLUNA `Sup.` DA TABELA 1 CONFERE COM O CHECKPOINT QUE O CODIGO CARREGA?

POR QUE EXISTE (08/09/2026). A regra de generalizacao exige «a menor correlacao em TODA base
em que o metodo nao foi ajustado». Isso so vale se a coluna `Sup.` estiver certa: um
checkpoint atribuido a base errada muda quais bases contam como NAO VISTAS, e portanto quem
passa na triagem. **Nada conferia essa coluna** — ela vinha da leitura de quem montou a
tabela.

⚠️ E ha uma distincao que so aparece quando se olha: o ARTIGO de cada modelo diz em que os
AUTORES treinaram; a coluna afirma qual CHECKPOINT LIBERADO foi usado. Sao coisas
diferentes. O LIQE, por exemplo, foi treinado no KADID-10k E no KonIQ-10k separadamente; o
que decide o veredito e qual dos dois o `pyiqa` carrega por padrao.

⭐ A FONTE CERTA e o registro do `pyiqa`, que e o codigo que de fato roda.
"""
import json
import re
from pathlib import Path

PY = Path('/data/projects/pipeline/.venv/lib/python3.12/site-packages/pyiqa')
SAIDA = Path(__file__).parent / 'o_que_as_fontes_dizem_do_treino.json'

# metrica no pyiqa -> (nome na Tabela 1, codigo `Sup.` que o artigo imprime)
TABELA = {
    'dbcnn': ('DBCNN', 'KQ'), 'hyperiqa': ('HyperIQA', 'KQ'), 'musiq': ('MUSIQ', 'KQ'),
    'topiq_nr': ('TOPIQ', 'KQ'), 'liqe': ('LIQE', 'KQ'), 'arniqa': ('ARNIQA', 'KQ'),
    'tres': ('TReS', 'KQ'), 'clipiqa': ('CLIP-IQA', 'OU'), 'clipiqa+': ('CLIP-IQA+', 'KQ'),
    'brisque': ('BRISQUE', 'LV'), 'niqe': ('NIQE', 'OU'),
}
# o que o registro nao revela, conferido em outro lugar do proprio codigo ou na fonte
FORA_DO_REGISTRO = {
    'hyperiqa': ('archs/hypernet_arch.py', 'HyperIQA-resnet50-koniq10k'),
    'clipiqa+': ('wang2023clipiqa.pdf', 'trained on KonIQ-10k'),
}


def registro():
    return (PY / 'default_model_configs.py').read_text(errors='ignore')


def dataset_de(metrica, t):
    """⚠️ o registro nao tem indentacao previsivel: pego do nome da metrica ate o inicio
    da PROXIMA chave de topo, e nao ate um `},` numa coluna fixa."""
    i = t.find("'" + metrica + "':")
    if i < 0:
        return None
    prox = re.search(r"\n    '[a-zA-Z0-9_+\-]+'\s*:", t[i + 5:])
    blk = ' '.join(t[i:i + 5 + (prox.start() if prox else 400)].split())
    for campo in ('pretrained', 'train_dataset', 'regressor_dataset', 'model_name'):
        d = re.search(r"'" + campo + r"'\s*:\s*'([^']+)'", blk)
        if d:
            return d.group(1)
    return ''


def main():
    t = registro()
    linhas, faltas = {}, []
    for met, (nome, cod) in TABELA.items():
        ds = dataset_de(met, t)
        onde = 'pyiqa/default_model_configs.py'
        if not ds and met in FORA_DO_REGISTRO:
            onde, ds = FORA_DO_REGISTRO[met]
        koniq = 'koniq' in (ds or '').lower()
        ok = (koniq and cod == 'KQ') or (not koniq and cod in ('OU', 'LV'))
        linhas[nome] = {'codigo_na_tabela': cod, 'checkpoint_ou_evidencia': ds or None,
                        'onde_foi_conferido': onde, 'confere': ok}
        if not ok:
            faltas.append('%s: tabela diz %s, o codigo carrega %r' % (nome, cod, ds))

    d = {'_o_que_e': __doc__,
         '_por_que_importa': 'a coluna Sup. decide quais bases contam como nao vistas, e '
                             'portanto quem passa na regra de generalizacao',
         'n_conferidos': len(linhas), 'n_divergem': len(faltas),
         'por_modelo': linhas, 'divergencias': faltas}
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    print('  %d codigos de supervisao conferidos contra o codigo que roda' % len(linhas))
    for n, v in linhas.items():
        print('    %s %-11s %-4s %-34s (%s)' % ('✅' if v['confere'] else '⛔', n,
              v['codigo_na_tabela'], str(v['checkpoint_ou_evidencia'])[:34],
              v['onde_foi_conferido'].split('/')[-1]))
    for f in faltas:
        print('    ⛔ %s' % f)
    return 1 if faltas else 0


if __name__ == '__main__':
    raise SystemExit(main())
