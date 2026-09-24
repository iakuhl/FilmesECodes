"""Testes de integração de `MembroRepositorioSqlite` contra um SQLite real."""

from datetime import date

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.membro_repository_sqlite import (
    MembroRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.membro import Membro


def _clube_salvo(engine: Engine) -> Clube:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    return clube


def test_salvar_e_buscar_por_id_preserva_apelido_e_ativo(engine: Engine) -> None:
    clube = _clube_salvo(engine)
    repositorio = MembroRepositorioSqlite(engine)
    membro = Membro.criar(
        clube_id=clube.id, nome="Ana", apelido="Aninha", data_ingresso=date(2024, 1, 1)
    )

    repositorio.salvar(membro)
    recuperado = repositorio.buscar_por_id(membro.id)

    assert recuperado is not None
    assert recuperado.nome == "Ana"
    assert recuperado.apelido == "Aninha"
    assert recuperado.ativo is True
    assert recuperado.data_ingresso == date(2024, 1, 1)


def test_membro_sem_apelido_recupera_none(engine: Engine) -> None:
    clube = _clube_salvo(engine)
    repositorio = MembroRepositorioSqlite(engine)
    membro = Membro.criar(clube_id=clube.id, nome="Bia", data_ingresso=date(2024, 1, 1))

    repositorio.salvar(membro)

    assert repositorio.buscar_por_id(membro.id).apelido is None  # type: ignore[union-attr]


def test_listar_ativos_por_clube_ignora_desativados(engine: Engine) -> None:
    clube = _clube_salvo(engine)
    repositorio = MembroRepositorioSqlite(engine)
    ativo = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    inativo = Membro.criar(clube_id=clube.id, nome="Bia", data_ingresso=date(2024, 1, 1))
    inativo.desativar()
    repositorio.salvar(ativo)
    repositorio.salvar(inativo)

    ativos = repositorio.listar_ativos_por_clube(clube.id)

    assert {membro.id for membro in ativos} == {ativo.id}
    assert len(repositorio.listar_por_clube(clube.id)) == 2
