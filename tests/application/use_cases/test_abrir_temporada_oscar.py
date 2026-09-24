"""Testes do caso de uso AbrirTemporadaOscar."""

from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.abrir_temporada_oscar import AbrirTemporadaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar
from tests.application.fakes.clube_repositorio_fake import ClubeRepositorioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)


def test_abrir_temporada_oscar_para_clube_existente(clube: Clube) -> None:
    clubes = ClubeRepositorioFake()
    clubes.salvar(clube)
    temporadas = TemporadaOscarRepositorioFake()
    caso_de_uso = AbrirTemporadaOscar(temporadas, clubes)

    temporada = caso_de_uso.executar(
        clube_id=clube.id, ano=2024, nome="Óscar do Filmes e Cubos 2024"
    )

    assert temporada.status is StatusTemporadaOscar.EM_PREPARACAO
    assert temporadas.buscar_por_id(temporada.id) is temporada


def test_abrir_temporada_para_clube_inexistente_levanta_erro() -> None:
    caso_de_uso = AbrirTemporadaOscar(TemporadaOscarRepositorioFake(), ClubeRepositorioFake())

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(clube_id=ClubeId(uuid4()), ano=2024, nome="Óscar 2024")
