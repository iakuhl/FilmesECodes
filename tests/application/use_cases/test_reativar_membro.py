"""Testes do caso de uso ReativarMembro."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.reativar_membro import ReativarMembro
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake


def test_reativar_membro_desativado(clube: Clube) -> None:
    membros = MembroRepositorioFake()
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membro.desativar()
    membros.salvar(membro)

    ReativarMembro(membros).executar(membro_id=membro.id)

    assert membros.buscar_por_id(membro.id).ativo is True  # type: ignore[union-attr]


def test_reativar_membro_inexistente_levanta_erro() -> None:
    with pytest.raises(EntidadeNaoEncontradaError):
        ReativarMembro(MembroRepositorioFake()).executar(membro_id=MembroId(uuid4()))
