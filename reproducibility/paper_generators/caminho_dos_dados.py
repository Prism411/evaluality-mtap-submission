"""Onde estao os JSON de medicao, sem depender do caminho de um computador.

POR QUE EXISTE (14/09/2026). Os dezenove geradores comecavam com
`QB = Path('/dados/Projetos/quality-benchmark')`. Num clone isso nao existe, e um revisor
apontou que a rota de reproducao publicada exigia editar o codigo.

⛔ E a primeira tentativa de conserto estava errada: escolher o PRIMEIRO diretorio que
EXISTE. O `derived_data/` ao lado do artigo existe e e PARCIAL, entao o gerador passou a
falhar num arquivo que estava no outro lugar. ⭐ A escolha tem de ser por CONTER O ARQUIVO
pedido, e nao por o diretorio existir.

Ordem: a variavel `EVALUALITY_DATA`, depois `derived_data/` ao lado e acima, depois a
arvore de trabalho. O primeiro que TEM o arquivo ganha.
"""
import os
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def candidatos():
    fora = os.environ.get('EVALUALITY_DATA')
    c = [Path(fora)] if fora else []
    return c + [AQUI / 'derived_data', AQUI.parent / 'derived_data',
                AQUI.parent / 'reproducibility' / 'derived_data',
                Path('/dados/Projetos/quality-benchmark')]


class Dados:
    """`DADOS / 'x.json'` devolve o primeiro candidato que TEM `x.json`."""

    def __truediv__(self, nome):
        for base in candidatos():
            p = base / nome
            if p.exists():
                return p
        # ⛔ nao devolve um caminho inventado: quem chamar recebe o erro com a lista
        raise FileNotFoundError(
            '%s nao esta em nenhum dos caminhos de dados: %s\n'
            'Defina EVALUALITY_DATA apontando para o diretorio que o contem.'
            % (nome, [str(x) for x in candidatos()]))

    def __repr__(self):
        return 'Dados(%s)' % ', '.join(str(x) for x in candidatos())


DADOS = Dados()


def _autoteste():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td) / 'so_aqui.json'
        q.write_text('{}')
        os.environ['EVALUALITY_DATA'] = td
        assert (DADOS / 'so_aqui.json') == q, '⛔ nao achou pela variavel de ambiente'
        try:
            DADOS / 'nao_existe_em_lugar_nenhum.json'
            raise AssertionError('⛔ devolveu caminho para arquivo inexistente')
        except FileNotFoundError as e:
            assert 'EVALUALITY_DATA' in str(e)
        del os.environ['EVALUALITY_DATA']
    print('  autoteste ✅ (acha pelo ambiente; inexistente estoura com a lista)')
    return True


if __name__ == '__main__':
    assert _autoteste()
    print('  candidatos:', [str(x) for x in candidatos()])
