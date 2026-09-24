"""Implementação SQLite (via SQLAlchemy Core) de `TrofeuRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import trofeus
from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
    TrofeuId,
)


class TrofeuRepositorioSqlite:
    """Persiste troféus em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, trofeu: Trofeu) -> None:
        upsert(self._engine, trofeus, _para_linha(trofeu))

    def buscar_por_categoria(self, categoria_id: CategoriaOscarId) -> Trofeu | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(trofeus.select().where(trofeus.c.categoria_id == str(categoria_id)))
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None


def _para_linha(trofeu: Trofeu) -> dict[str, Any]:
    return {
        "id": str(trofeu.id),
        "categoria_id": str(trofeu.categoria_id),
        "nomeacao_vencedora_id": str(trofeu.nomeacao_vencedora_id),
        "membro_vencedor_id": str(trofeu.membro_vencedor_id),
        "data_apuracao": trofeu.data_apuracao,
    }


def _para_entidade(linha: RowMapping) -> Trofeu:
    return Trofeu(
        id=TrofeuId(UUID(linha["id"])),
        categoria_id=CategoriaOscarId(UUID(linha["categoria_id"])),
        nomeacao_vencedora_id=NomeacaoOscarId(UUID(linha["nomeacao_vencedora_id"])),
        membro_vencedor_id=MembroId(UUID(linha["membro_vencedor_id"])),
        data_apuracao=linha["data_apuracao"],
    )
