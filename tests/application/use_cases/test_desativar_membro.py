"""Testes do caso de uso DesativarMembro."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.desativar_membro import DesativarMembro
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake


def test_desativar_membro_existente(clube: Clube) -> None:
    membros = MembroRepositorioFake()
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro)
    caso_de_uso = DesativarMembro(membros)

    caso_de_uso.executar(membro_id=membro.id)

    assert membros.buscar_por_id(membro.id).ativo is False  # type: ignore[union-attr]


def test_desativar_membro_inexistente_levanta_erro() -> None:
    caso_de_uso = DesativarMembro(MembroRepositorioFake())

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(membro_id=MembroId(uuid4()))
