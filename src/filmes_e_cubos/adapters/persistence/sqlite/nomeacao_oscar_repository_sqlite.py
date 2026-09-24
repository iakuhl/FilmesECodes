"""Implementação SQLite (via SQLAlchemy Core) de `NomeacaoOscarRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import nomeacoes_oscar
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    NomeacaoOscarId,
)


class NomeacaoOscarRepositorioSqlite:
    """Persiste nomeações do Óscar em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, nomeacao: NomeacaoOscar) -> None:
        upsert(self._engine, nomeacoes_oscar, _para_linha(nomeacao))

    def buscar_por_id(self, nomeacao_id: NomeacaoOscarId) -> NomeacaoOscar | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    nomeacoes_oscar.select().where(nomeacoes_oscar.c.id == str(nomeacao_id))
                )
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def listar_por_categoria(self, categoria_id: CategoriaOscarId) -> list[NomeacaoOscar]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(
                    nomeacoes_oscar.select().where(
                        nomeacoes_oscar.c.categoria_id == str(categoria_id)
                    )
                )
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(nomeacao: NomeacaoOscar) -> dict[str, Any]:
    indicador = nomeacao.indicado_por_membro_id
    return {
        "id": str(nomeacao.id),
        "categoria_id": str(nomeacao.categoria_id),
        "filme_id": str(nomeacao.filme_id),
        "indicado_por_membro_id": str(indicador) if indicador is not None else None,
    }


def _para_entidade(linha: RowMapping) -> NomeacaoOscar:
    indicador = linha["indicado_por_membro_id"]
    return NomeacaoOscar(
        id=NomeacaoOscarId(UUID(linha["id"])),
        categoria_id=CategoriaOscarId(UUID(linha["categoria_id"])),
        filme_id=FilmeId(UUID(linha["filme_id"])),
        indicado_por_membro_id=MembroId(UUID(indicador)) if indicador is not None else None,
    )
