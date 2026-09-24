"""Implementação SQLite (via SQLAlchemy Core) de `RodadaRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping, func, select

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import rodadas
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, RodadaId
from filmes_e_cubos.domain.value_objects.status import StatusRodada


class RodadaRepositorioSqlite:
    """Persiste rodadas em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, rodada: Rodada) -> None:
        upsert(self._engine, rodadas, _para_linha(rodada))

    def buscar_por_id(self, rodada_id: RodadaId) -> Rodada | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(rodadas.select().where(rodadas.c.id == str(rodada_id)))
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def buscar_aberta_por_clube(self, clube_id: ClubeId) -> Rodada | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    rodadas.select().where(
                        rodadas.c.clube_id == str(clube_id),
                        rodadas.c.status == StatusRodada.ABERTA.name,
                    )
                )
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def contar_por_clube(self, clube_id: ClubeId) -> int:
        with self._engine.connect() as conexao:
            total = conexao.execute(
                select(func.count()).select_from(rodadas).where(rodadas.c.clube_id == str(clube_id))
            ).scalar_one()
        return int(total)

    def listar_por_clube(self, clube_id: ClubeId) -> list[Rodada]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(
                    rodadas.select()
                    .where(rodadas.c.clube_id == str(clube_id))
                    .order_by(rodadas.c.numero)
                )
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(rodada: Rodada) -> dict[str, Any]:
    return {
        "id": str(rodada.id),
        "clube_id": str(rodada.clube_id),
        "numero": rodada.numero,
        "status": rodada.status.name,
        "data_inicio": rodada.data_inicio,
        "data_encerramento": rodada.data_encerramento,
    }


def _para_entidade(linha: RowMapping) -> Rodada:
    return Rodada(
        id=RodadaId(UUID(linha["id"])),
        clube_id=ClubeId(UUID(linha["clube_id"])),
        numero=linha["numero"],
        status=StatusRodada[linha["status"]],
        data_inicio=linha["data_inicio"],
        data_encerramento=linha["data_encerramento"],
    )
