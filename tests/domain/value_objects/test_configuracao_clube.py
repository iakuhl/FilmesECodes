"""Testes do value object ConfiguracaoClube."""

from decimal import Decimal

import pytest

from filmes_e_cubos.domain.exceptions.clube import TamanhoRodadaInvalidoError
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao


def test_configuracao_padrao_tem_rodadas_de_cinco_indicacoes() -> None:
    configuracao = ConfiguracaoClube.padrao()

    assert configuracao.tamanho_rodada == 5
    assert configuracao.escala_avaliacao == EscalaAvaliacao.padrao()


@pytest.mark.parametrize("tamanho_rodada", [0, -1, -5])
def test_tamanho_de_rodada_nao_positivo_levanta_erro(tamanho_rodada: int) -> None:
    with pytest.raises(TamanhoRodadaInvalidoError):
        ConfiguracaoClube(tamanho_rodada=tamanho_rodada, escala_avaliacao=EscalaAvaliacao.padrao())


def test_configuracao_aceita_tamanho_de_rodada_diferente_do_padrao() -> None:
    configuracao = ConfiguracaoClube(
        tamanho_rodada=8,
        escala_avaliacao=EscalaAvaliacao(
            nota_minima=Decimal("1"), nota_maxima=Decimal("10"), passo=Decimal("1")
        ),
    )

    assert configuracao.tamanho_rodada == 8
