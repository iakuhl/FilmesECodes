"""Implementação SQLite (via SQLAlchemy Core) de `SessaoRepository`."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import (
    sessao_membros_presentes,
    sessoes_exibicao,
)
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.value_objects.identificadores import (
    IndicacaoId,
    MembroId,
    SessaoExibicaoId,
)
from filmes_e_cubos.domain.value_objects.media_das_notas import MediaDasNotas


class SessaoRepositorioSqlite:
    """Persiste sessões de exibição (e a lista de presentes) em SQLite."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, sessao: SessaoExibicao) -> None:
        upsert(self._engine, sessoes_exibicao, _para_linha(sessao))
        with self._engine.begin() as conexao:
            conexao.execute(
                sessao_membros_presentes.delete().where(
                    sessao_membros_presentes.c.sessao_id == str(sessao.id)
                )
            )
            if sessao.membros_presentes:
                conexao.execute(
                    sessao_membros_presentes.insert(),
                    [
                        {"sessao_id": str(sessao.id), "membro_id": str(membro_id)}
                        for membro_id in sessao.membros_presentes
                    ],
                )

    def buscar_por_id(self, sessao_id: SessaoExibicaoId) -> SessaoExibicao | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    sessoes_exibicao.select().where(sessoes_exibicao.c.id == str(sessao_id))
                )
                .mappings()
                .first()
            )
            if linha is None:
                return None
            presentes = self._buscar_presentes(conexao, sessao_id)
        return _para_entidade(linha, presentes)

    def buscar_por_indicacao(self, indicacao_id: IndicacaoId) -> SessaoExibicao | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    sessoes_exibicao.select().where(
                        sessoes_exibicao.c.indicacao_id == str(indicacao_id)
                    )
                )
                .mappings()
                .first()
            )
            if linha is None:
                return None
            presentes = self._buscar_presentes(conexao, SessaoExibicaoId(UUID(linha["id"])))
        return _para_entidade(linha, presentes)

    def _buscar_presentes(
        self, conexao: Connection, sessao_id: SessaoExibicaoId
    ) -> frozenset[MembroId]:
        linhas = (
            conexao.execute(
                sessao_membros_presentes.select().where(
                    sessao_membros_presentes.c.sessao_id == str(sessao_id)
                )
            )
            .mappings()
            .all()
        )
        return frozenset(MembroId(UUID(linha["membro_id"])) for linha in linhas)


def _para_linha(sessao: SessaoExibicao) -> dict[str, Any]:
    media = sessao.media_das_notas
    return {
        "id": str(sessao.id),
        "indicacao_id": str(sessao.indicacao_id),
        "data_sessao": sessao.data_sessao,
        "soma_das_notas": str(media.soma) if media is not None else "0",
        "quantidade_de_notas": media.quantidade if media is not None else 0,
    }


def _para_entidade(linha: RowMapping, presentes: frozenset[MembroId]) -> SessaoExibicao:
    quantidade = linha["quantidade_de_notas"]
    return SessaoExibicao(
        id=SessaoExibicaoId(UUID(linha["id"])),
        indicacao_id=IndicacaoId(UUID(linha["indicacao_id"])),
        data_sessao=linha["data_sessao"],
        membros_presentes=presentes,
        media_das_notas=(
            MediaDasNotas(soma=Decimal(linha["soma_das_notas"]), quantidade=quantidade)
            if quantidade > 0
            else None
        ),
    )
