"""Testes da entidade Rodada."""

from datetime import date

import pytest

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaEncerradaError
from filmes_e_cubos.domain.value_objects.status import StatusRodada


def test_abrir_rodada_nasce_aberta(clube: Clube) -> None:
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))

    assert rodada.status is StatusRodada.ABERTA
    assert rodada.esta_aberta is True
    assert rodada.data_encerramento is None


def test_encerrar_rodada_aberta_transiciona_para_encerrada(clube: Clube) -> None:
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))

    rodada.encerrar(data_encerramento=date(2024, 3, 1))

    assert rodada.status is StatusRodada.ENCERRADA
    assert rodada.esta_aberta is False
    assert rodada.data_encerramento == date(2024, 3, 1)


def test_encerrar_rodada_ja_encerrada_levanta_erro(clube: Clube) -> None:
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodada.encerrar(data_encerramento=date(2024, 3, 1))

    with pytest.raises(RodadaJaEncerradaError):
        rodada.encerrar(data_encerramento=date(2024, 3, 2))
