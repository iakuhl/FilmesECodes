"""Testes da entidade Clube."""

import pytest

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.exceptions.clube import NomeClubeObrigatorioError
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube


def test_criar_clube_com_nome_valido() -> None:
    clube = Clube.criar(nome="Filmes e Cubos")

    assert clube.nome == "Filmes e Cubos"
    assert clube.configuracao == ConfiguracaoClube.padrao()


@pytest.mark.parametrize("nome_invalido", ["", "   "])
def test_criar_clube_sem_nome_levanta_erro(nome_invalido: str) -> None:
    with pytest.raises(NomeClubeObrigatorioError):
        Clube.criar(nome=nome_invalido)


def test_atualizar_configuracao_substitui_configuracao_atual() -> None:
    clube = Clube.criar(nome="Filmes e Cubos")
    nova_configuracao = ConfiguracaoClube(
        tamanho_rodada=6, escala_avaliacao=ConfiguracaoClube.padrao().escala_avaliacao
    )

    clube.atualizar_configuracao(nova_configuracao)

    assert clube.configuracao.tamanho_rodada == 6
