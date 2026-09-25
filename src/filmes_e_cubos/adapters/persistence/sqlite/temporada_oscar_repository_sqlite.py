"""Implementação SQLite (via SQLAlchemy Core) de `TemporadaOscarRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import temporadas_oscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar


class TemporadaOscarRepositorioSqlite:
    """Persiste temporadas do Óscar em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, temporada: TemporadaOscar) -> None:
        upsert(self._engine, temporadas_oscar, _para_linha(temporada))

    def buscar_por_id(self, temporada_id: TemporadaOscarId) -> TemporadaOscar | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    temporadas_oscar.select().where(temporadas_oscar.c.id == str(temporada_id))
                )
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def buscar_por_clube_e_ano(self, clube_id: ClubeId, ano: int) -> TemporadaOscar | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    temporadas_oscar.select().where(
                        temporadas_oscar.c.clube_id == str(clube_id),
                        temporadas_oscar.c.ano == ano,
                    )
                )
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def listar_por_clube(self, clube_id: ClubeId) -> list[TemporadaOscar]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(
                    temporadas_oscar.select().where(temporadas_oscar.c.clube_id == str(clube_id))
                )
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(temporada: TemporadaOscar) -> dict[str, Any]:
    return {
        "id": str(temporada.id),
        "clube_id": str(temporada.clube_id),
        "ano": temporada.ano,
        "nome": temporada.nome,
        "status": temporada.status.name,
        "data_evento": temporada.data_evento,
        "nomeacoes_por_categoria": temporada.nomeacoes_por_categoria,
    }


def _para_entidade(linha: RowMapping) -> TemporadaOscar:
    return TemporadaOscar(
        id=TemporadaOscarId(UUID(linha["id"])),
        clube_id=ClubeId(UUID(linha["clube_id"])),
        ano=linha["ano"],
        nome=linha["nome"],
        status=StatusTemporadaOscar[linha["status"]],
        data_evento=linha["data_evento"],
        nomeacoes_por_categoria=linha["nomeacoes_por_categoria"],
    )
