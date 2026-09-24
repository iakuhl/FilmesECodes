"""Testes da entidade CategoriaOscar."""

from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.exceptions.oscar import NomeCategoriaObrigatorioError
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


def test_criar_categoria_variavel_com_nome_valido() -> None:
    categoria = CategoriaOscar.criar(
        temporada_id=TemporadaOscarId(uuid4()),
        nome="Melhor veículo",
        tipo=TipoCategoriaOscar.VARIAVEL,
    )

    assert categoria.nome == "Melhor veículo"
    assert categoria.tipo is TipoCategoriaOscar.VARIAVEL


@pytest.mark.parametrize("nome_invalido", ["", "   "])
def test_criar_categoria_sem_nome_levanta_erro(nome_invalido: str) -> None:
    with pytest.raises(NomeCategoriaObrigatorioError):
        CategoriaOscar.criar(
            temporada_id=TemporadaOscarId(uuid4()),
            nome=nome_invalido,
            tipo=TipoCategoriaOscar.FIXA,
        )
