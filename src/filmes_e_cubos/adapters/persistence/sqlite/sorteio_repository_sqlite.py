"""Implementação SQLite (via SQLAlchemy Core) de `SorteioRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import sorteios
from filmes_e_cubos.domain.entities.sorteio import Sorteio
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, RodadaId, SorteioId


class SorteioRepositorioSqlite:
    """Persiste sorteios em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, sorteio: Sorteio) -> None:
        upsert(self._engine, sorteios, _para_linha(sorteio))

    def listar_por_rodada(self, rodada_id: RodadaId) -> list[Sorteio]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(sorteios.select().where(sorteios.c.rodada_id == str(rodada_id)))
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(sorteio: Sorteio) -> dict[str, Any]:
    return {
        "id": str(sorteio.id),
        "rodada_id": str(sorteio.rodada_id),
        "indicacao_sorteada_id": str(sorteio.indicacao_sorteada_id),
        "data_sorteio": sorteio.data_sorteio,
        "metodo": sorteio.metodo,
    }


def _para_entidade(linha: RowMapping) -> Sorteio:
    return Sorteio(
        id=SorteioId(UUID(linha["id"])),
        rodada_id=RodadaId(UUID(linha["rodada_id"])),
        indicacao_sorteada_id=IndicacaoId(UUID(linha["indicacao_sorteada_id"])),
        data_sorteio=linha["data_sorteio"],
        metodo=linha["metodo"],
    )
