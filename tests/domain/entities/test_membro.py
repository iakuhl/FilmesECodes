"""Testes da entidade Membro."""

from datetime import date

import pytest

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.exceptions.membro import NomeMembroObrigatorioError


def test_criar_membro_nasce_ativo(clube: Clube) -> None:
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))

    assert membro.ativo is True
    assert membro.clube_id == clube.id


@pytest.mark.parametrize("nome_invalido", ["", "   "])
def test_criar_membro_sem_nome_levanta_erro(clube: Clube, nome_invalido: str) -> None:
    with pytest.raises(NomeMembroObrigatorioError):
        Membro.criar(clube_id=clube.id, nome=nome_invalido, data_ingresso=date(2024, 1, 1))


def test_desativar_marca_membro_como_inativo(clube: Clube) -> None:
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))

    membro.desativar()

    assert membro.ativo is False


def test_reativar_marca_membro_como_ativo_novamente(clube: Clube) -> None:
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membro.desativar()

    membro.reativar()

    assert membro.ativo is True
