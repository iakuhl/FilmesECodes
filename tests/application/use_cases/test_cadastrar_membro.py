"""Testes do caso de uso CadastrarMembro."""

from datetime import datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.cadastrar_membro import CadastrarMembro
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId
from tests.application.fakes.clube_repositorio_fake import ClubeRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake


def test_cadastrar_membro_em_clube_existente(clube: Clube) -> None:
    clubes = ClubeRepositorioFake()
    clubes.salvar(clube)
    membros = MembroRepositorioFake()
    caso_de_uso = CadastrarMembro(membros, clubes, RelogioFake(datetime(2024, 1, 1)))

    membro = caso_de_uso.executar(clube_id=clube.id, nome="Ana")

    assert membros.buscar_por_id(membro.id) is membro
    assert membro.ativo is True
    assert membro.data_ingresso == datetime(2024, 1, 1).date()


def test_cadastrar_membro_em_clube_inexistente_levanta_erro() -> None:
    caso_de_uso = CadastrarMembro(
        MembroRepositorioFake(), ClubeRepositorioFake(), RelogioFake(datetime(2024, 1, 1))
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(clube_id=ClubeId(uuid4()), nome="Ana")
