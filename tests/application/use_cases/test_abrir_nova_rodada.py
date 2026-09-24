"""Testes do caso de uso AbrirNovaRodada."""

from datetime import datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.abrir_nova_rodada import AbrirNovaRodada
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaAbertaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId
from tests.application.fakes.clube_repositorio_fake import ClubeRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake


def test_abrir_primeira_rodada_do_clube(clube: Clube) -> None:
    clubes = ClubeRepositorioFake()
    clubes.salvar(clube)
    rodadas = RodadaRepositorioFake()
    caso_de_uso = AbrirNovaRodada(rodadas, clubes, RelogioFake(datetime(2024, 1, 1)))

    rodada = caso_de_uso.executar(clube_id=clube.id)

    assert rodada.numero == 1
    assert rodada.esta_aberta is True


def test_abrir_rodada_quando_ja_existe_uma_aberta_levanta_erro(clube: Clube) -> None:
    clubes = ClubeRepositorioFake()
    clubes.salvar(clube)
    rodadas = RodadaRepositorioFake()
    caso_de_uso = AbrirNovaRodada(rodadas, clubes, RelogioFake(datetime(2024, 1, 1)))
    caso_de_uso.executar(clube_id=clube.id)

    with pytest.raises(RodadaJaAbertaError):
        caso_de_uso.executar(clube_id=clube.id)


def test_abrir_rodada_para_clube_inexistente_levanta_erro() -> None:
    caso_de_uso = AbrirNovaRodada(
        RodadaRepositorioFake(), ClubeRepositorioFake(), RelogioFake(datetime(2024, 1, 1))
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(clube_id=ClubeId(uuid4()))
