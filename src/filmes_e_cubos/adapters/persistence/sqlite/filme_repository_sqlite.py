"""Implementação SQLite (via SQLAlchemy Core) de `FilmeRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import filmes
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId


class FilmeRepositorioSqlite:
    """Persiste filmes em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, filme: Filme) -> None:
        upsert(self._engine, filmes, _para_linha(filme))

    def buscar_por_id(self, filme_id: FilmeId) -> Filme | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(filmes.select().where(filmes.c.id == str(filme_id)))
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def listar_todos(self) -> list[Filme]:
        with self._engine.connect() as conexao:
            linhas = conexao.execute(filmes.select()).mappings().all()
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(filme: Filme) -> dict[str, Any]:
    return {
        "id": str(filme.id),
        "titulo": filme.titulo,
        "ano_lancamento": filme.ano_lancamento,
        "diretor": filme.diretor,
        "identificador_externo": filme.identificador_externo,
    }


def _para_entidade(linha: RowMapping) -> Filme:
    return Filme(
        id=FilmeId(UUID(linha["id"])),
        titulo=linha["titulo"],
        ano_lancamento=linha["ano_lancamento"],
        diretor=linha["diretor"],
        identificador_externo=linha["identificador_externo"],
    )
