"""Implementação SQLite (via SQLAlchemy Core) de `MembroRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import membros
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, MembroId


class MembroRepositorioSqlite:
    """Persiste membros em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, membro: Membro) -> None:
        upsert(self._engine, membros, _para_linha(membro))

    def buscar_por_id(self, membro_id: MembroId) -> Membro | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(membros.select().where(membros.c.id == str(membro_id)))
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def listar_ativos_por_clube(self, clube_id: ClubeId) -> list[Membro]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(
                    membros.select().where(
                        membros.c.clube_id == str(clube_id), membros.c.ativo.is_(True)
                    )
                )
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]

    def listar_por_clube(self, clube_id: ClubeId) -> list[Membro]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(membros.select().where(membros.c.clube_id == str(clube_id)))
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(membro: Membro) -> dict[str, Any]:
    return {
        "id": str(membro.id),
        "clube_id": str(membro.clube_id),
        "nome": membro.nome,
        "apelido": membro.apelido,
        "data_ingresso": membro.data_ingresso,
        "ativo": membro.ativo,
    }


def _para_entidade(linha: RowMapping) -> Membro:
    return Membro(
        id=MembroId(UUID(linha["id"])),
        clube_id=ClubeId(UUID(linha["clube_id"])),
        nome=linha["nome"],
        apelido=linha["apelido"],
        data_ingresso=linha["data_ingresso"],
        ativo=bool(linha["ativo"]),
    )
