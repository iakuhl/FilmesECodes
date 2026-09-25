"""Testes de integração de `FilmeRepositorioSqlite` contra um SQLite real."""

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.filme_repository_sqlite import (
    FilmeRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.filme import Filme


def test_salvar_e_buscar_por_id_preserva_campos_opcionais(engine: Engine) -> None:
    repositorio = FilmeRepositorioSqlite(engine)
    filme = Filme.criar(
        titulo="Duna", ano_lancamento=2021, diretor="Denis Villeneuve", duracao_minutos=155
    )

    repositorio.salvar(filme)
    recuperado = repositorio.buscar_por_id(filme.id)

    assert recuperado is not None
    assert recuperado.titulo == "Duna"
    assert recuperado.ano_lancamento == 2021
    assert recuperado.diretor == "Denis Villeneuve"
    assert recuperado.duracao_minutos == 155


def test_filme_apenas_com_titulo_recupera_campos_opcionais_como_none(engine: Engine) -> None:
    repositorio = FilmeRepositorioSqlite(engine)
    filme = Filme.criar(titulo="Arrival")

    repositorio.salvar(filme)
    recuperado = repositorio.buscar_por_id(filme.id)

    assert recuperado is not None
    assert recuperado.ano_lancamento is None
    assert recuperado.diretor is None


def test_listar_todos_retorna_todos_os_filmes(engine: Engine) -> None:
    repositorio = FilmeRepositorioSqlite(engine)
    repositorio.salvar(Filme.criar(titulo="Duna"))
    repositorio.salvar(Filme.criar(titulo="Arrival"))

    assert {filme.titulo for filme in repositorio.listar_todos()} == {"Duna", "Arrival"}
