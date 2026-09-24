"""Testes do caso de uso DefinirCategoriaOscar."""

from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.definir_categoria_oscar import DefinirCategoriaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)


def test_definir_categoria_em_temporada_existente(clube: Clube) -> None:
    temporadas = TemporadaOscarRepositorioFake()
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    temporadas.salvar(temporada)
    categorias = CategoriaOscarRepositorioFake()
    caso_de_uso = DefinirCategoriaOscar(categorias, temporadas)

    categoria = caso_de_uso.executar(
        temporada_id=temporada.id, nome="Melhor veículo", tipo=TipoCategoriaOscar.VARIAVEL
    )

    assert categorias.buscar_por_id(categoria.id) is categoria


def test_definir_categoria_em_temporada_inexistente_levanta_erro() -> None:
    caso_de_uso = DefinirCategoriaOscar(
        CategoriaOscarRepositorioFake(), TemporadaOscarRepositorioFake()
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(
            temporada_id=TemporadaOscarId(uuid4()),
            nome="Melhor veículo",
            tipo=TipoCategoriaOscar.VARIAVEL,
        )
