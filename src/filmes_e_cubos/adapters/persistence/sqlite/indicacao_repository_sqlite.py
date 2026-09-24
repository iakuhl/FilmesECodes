"""Implementação SQLite (via SQLAlchemy Core) de `IndicacaoRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import indicacoes
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.value_objects.identificadores import (
    FilmeId,
    IndicacaoId,
    MembroId,
    RodadaId,
)
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao
from filmes_e_cubos.domain.value_objects.tipo_indicacao import TipoIndicacao


class IndicacaoRepositorioSqlite:
    """Persiste indicações em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, indicacao: Indicacao) -> None:
        upsert(self._engine, indicacoes, _para_linha(indicacao))

    def buscar_por_id(self, indicacao_id: IndicacaoId) -> Indicacao | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(indicacoes.select().where(indicacoes.c.id == str(indicacao_id)))
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def listar_por_rodada(self, rodada_id: RodadaId) -> list[Indicacao]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(indicacoes.select().where(indicacoes.c.rodada_id == str(rodada_id)))
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]

    def listar_assistidas_por_filme(self, filme_id: FilmeId) -> list[Indicacao]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(
                    indicacoes.select().where(
                        indicacoes.c.filme_id == str(filme_id),
                        indicacoes.c.status == StatusIndicacao.ASSISTIDA.name,
                    )
                )
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(indicacao: Indicacao) -> dict[str, Any]:
    return {
        "id": str(indicacao.id),
        "rodada_id": str(indicacao.rodada_id),
        "membro_id": str(indicacao.membro_id) if indicacao.membro_id is not None else None,
        "filme_id": str(indicacao.filme_id),
        "tipo": indicacao.tipo.name,
        "status": indicacao.status.name,
        "data_indicacao": indicacao.data_indicacao,
    }


def _para_entidade(linha: RowMapping) -> Indicacao:
    membro_id = MembroId(UUID(linha["membro_id"])) if linha["membro_id"] is not None else None
    return Indicacao(
        id=IndicacaoId(UUID(linha["id"])),
        rodada_id=RodadaId(UUID(linha["rodada_id"])),
        membro_id=membro_id,
        filme_id=FilmeId(UUID(linha["filme_id"])),
        data_indicacao=linha["data_indicacao"],
        tipo=TipoIndicacao[linha["tipo"]],
        status=StatusIndicacao[linha["status"]],
    )
