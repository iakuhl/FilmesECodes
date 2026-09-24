"""Implementação SQLite (via SQLAlchemy Core) de `CategoriaOscarRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import categorias_oscar
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


class CategoriaOscarRepositorioSqlite:
    """Persiste categorias do Óscar em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, categoria: CategoriaOscar) -> None:
        upsert(self._engine, categorias_oscar, _para_linha(categoria))

    def buscar_por_id(self, categoria_id: CategoriaOscarId) -> CategoriaOscar | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    categorias_oscar.select().where(categorias_oscar.c.id == str(categoria_id))
                )
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def listar_por_temporada(self, temporada_id: TemporadaOscarId) -> list[CategoriaOscar]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(
                    categorias_oscar.select().where(
                        categorias_oscar.c.temporada_id == str(temporada_id)
                    )
                )
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(categoria: CategoriaOscar) -> dict[str, Any]:
    return {
        "id": str(categoria.id),
        "temporada_id": str(categoria.temporada_id),
        "nome": categoria.nome,
        "tipo": categoria.tipo.name,
        "descricao": categoria.descricao,
    }


def _para_entidade(linha: RowMapping) -> CategoriaOscar:
    return CategoriaOscar(
        id=CategoriaOscarId(UUID(linha["id"])),
        temporada_id=TemporadaOscarId(UUID(linha["temporada_id"])),
        nome=linha["nome"],
        tipo=TipoCategoriaOscar[linha["tipo"]],
        descricao=linha["descricao"],
    )
