"""Testes do caso de uso DefinirDataEventoOscar."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.definir_data_evento_oscar import (
    DefinirDataEventoOscar,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)


def test_marca_a_data_do_evento(clube: Clube) -> None:
    temporadas = TemporadaOscarRepositorioFake()
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    temporadas.salvar(temporada)

    DefinirDataEventoOscar(temporadas).executar(
        temporada_id=temporada.id, data_evento=date(2025, 1, 18)
    )

    salva = temporadas.buscar_por_id(temporada.id)
    assert salva is not None
    assert salva.data_evento == date(2025, 1, 18)


def test_temporada_inexistente_levanta_erro() -> None:
    with pytest.raises(EntidadeNaoEncontradaError):
        DefinirDataEventoOscar(TemporadaOscarRepositorioFake()).executar(
            temporada_id=TemporadaOscarId(uuid4()), data_evento=date(2025, 1, 18)
        )
