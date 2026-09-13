"""⛔ ENTRADA AUSENTE FALHA ALTO, E RESULTADO PARCIAL NAO SOBRESCREVE COMPLETO.

POR QUE EXISTE (13/09/2026, apos parecer de revisor). O README deste repositorio declarava,
honestamente, um defeito real: «Scripts in the first two groups can still exit successfully
while writing a partial result when their inputs are missing: running the whole directory in
one pass let a two-cluster control file overwrite the shipped forty-two-cluster one and break
a downstream script.»

⚠️ O revisor apontou a assimetria certa: precisar de midia ou pesos que nao se redistribuem
e limitacao NORMAL; terminar com status de sucesso e substituir em silencio um resultado
completo por um parcial e defeito CORRIGIVEL. Este modulo corrige o segundo.

COMO USAR, em qualquer script deste diretorio:

    from exige import entrada, grava

    caminho = entrada('derived_data/synth_scores.json')   # ausente -> SystemExit
    grava('derived_data/x.json', dados)                   # encolher -> SystemExit

⭐ A regra de `grava` e deliberadamente conservadora: se o arquivo ja existe e o novo
conteudo tem MENOS registros no mesmo nivel, a escrita e RECUSADA. Encolher pode ser
legitimo, e nesse caso se declara com `permitir_encolher=True`, que fica no codigo e no
diff em vez de acontecer em silencio.
"""
import json
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def entrada(caminho, dica=''):
    """O caminho, se existir e nao estiver vazio. Senao, SystemExit com o motivo."""
    p = Path(caminho)
    if not p.is_absolute():
        p = AQUI / p
    if not p.exists():
        raise SystemExit(
            '⛔ ENTRADA AUSENTE: %s\n'
            '   Este script nao produz resultado parcial: ele para aqui.\n'
            '   %s' % (p, dica or 'Rode-o numa arvore onde essa entrada exista.'))
    if p.is_file() and p.stat().st_size == 0:
        raise SystemExit('⛔ ENTRADA VAZIA: %s' % p)
    return p


def _tamanho(o):
    """Quantos registros o conteudo tem no nivel de topo, para comparar com o que ja existe."""
    if isinstance(o, dict):
        # ⚠️ chaves de metadado nao contam: um arquivo com `_o_que_e` e mais nada e vazio
        uteis = [k for k in o if not str(k).startswith('_')]
        if len(uteis) == 1 and isinstance(o[uteis[0]], (dict, list)):
            return len(o[uteis[0]])
        return len(uteis)
    if isinstance(o, list):
        return len(o)
    return 1


def grava(caminho, dados, permitir_encolher=False, indent=2):
    """Grava JSON, RECUSANDO encolher um arquivo que ja existe.

    Foi assim que um controle de dois clusters sobrescreveu o de quarenta e dois.
    """
    p = Path(caminho)
    if not p.is_absolute():
        p = AQUI / p
    novo = _tamanho(dados)
    if p.exists() and not permitir_encolher:
        try:
            velho = _tamanho(json.loads(p.read_text(encoding='utf-8')))
        except Exception:
            velho = None
        if velho is not None and novo < velho:
            raise SystemExit(
                '⛔ ESCRITA RECUSADA: %s\n'
                '   o arquivo em disco tem %d registro(s) e o novo conteudo tem %d.\n'
                '   Encolher um resultado publicado costuma significar entrada ausente.\n'
                '   Se a reducao e intencional, passe permitir_encolher=True, que fica\n'
                '   declarado no codigo e no diff.' % (p, velho, novo))
    tmp = p.with_suffix(p.suffix + '.parcial')
    tmp.write_text(json.dumps(dados, indent=indent, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, p)          # ⭐ troca atomica: nunca deixa um arquivo meio escrito
    return p


def _autoteste():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td) / 'x.json'
        grava(q, {'dados': {str(i): i for i in range(42)}})
        assert _tamanho(json.loads(q.read_text())) == 42
        # ⛔ o defeito real: dois clusters onde havia quarenta e dois
        try:
            grava(q, {'dados': {'a': 1, 'b': 2}})
            raise AssertionError('⛔ NAO recusou encolher de 42 para 2')
        except SystemExit as e:
            assert 'ESCRITA RECUSADA' in str(e)
        # e o encolhimento declarado passa
        grava(q, {'dados': {'a': 1, 'b': 2}}, permitir_encolher=True)
        assert _tamanho(json.loads(q.read_text())) == 2
        # entrada ausente para alto
        try:
            entrada(Path(td) / 'nao_existe.json')
            raise AssertionError('⛔ NAO parou numa entrada ausente')
        except SystemExit as e:
            assert 'ENTRADA AUSENTE' in str(e)
        # e o metadado nao conta como registro
        assert _tamanho({'_o_que_e': 'x', 'dados': {'a': 1}}) == 1
    print('  autoteste ✅ (encolher de 42 para 2 REPROVA; declarado passa; ausente para alto)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    print('  ✅ exige.py pronto para uso')
    sys.exit(0)
