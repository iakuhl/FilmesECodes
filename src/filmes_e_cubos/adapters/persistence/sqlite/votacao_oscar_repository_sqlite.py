"""Implementação SQLite (via SQLAlchemy Core) de `VotacaoOscarRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert_na_conexao
from filmes_e_cubos.adapters.persistence.sqlite.esquema import votacao_eleitores, votacoes_oscar
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import (
    MembroId,
    TemporadaOscarId,
    VotacaoOscarId,
)


class VotacaoOscarRepositorioSqlite:
    """Persiste a votação de cada edição (e os seus eleitores) em SQLite."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, votacao: VotacaoOscar) -> None:
        with self._engine.begin() as conexao:
            upsert_na_conexao(conexao, votacoes_oscar, _para_linha(votacao))
            conexao.execute(
                votacao_eleitores.delete().where(votacao_eleitores.c.votacao_id == str(votacao.id))
            )
            if votacao.eleitores:
                conexao.execute(
                    votacao_eleitores.insert(),
                    [
                        {"votacao_id": str(votacao.id), "membro_id": str(membro_id)}
                        for membro_id in votacao.eleitores
                    ],
                )

    def buscar_por_temporada(self, temporada_id: TemporadaOscarId) -> VotacaoOscar | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    votacoes_oscar.select().where(
                        votacoes_oscar.c.temporada_id == str(temporada_id)
                    )
                )
                .mappings()
                .first()
            )
            if linha is None:
                return None
            eleitores = conexao.execute(
                votacao_eleitores.select().where(votacao_eleitores.c.votacao_id == linha["id"])
            ).mappings()
            return _para_entidade(
                linha, [MembroId(UUID(eleitor["membro_id"])) for eleitor in eleitores]
            )


def _para_linha(votacao: VotacaoOscar) -> dict[str, Any]:
    return {
        "id": str(votacao.id),
        "temporada_id": str(votacao.temporada_id),
        "iniciada_em": votacao.iniciada_em,
        "turno_atual": votacao.turno_atual,
        "encerrada_em": votacao.encerrada_em,
    }


def _para_entidade(linha: RowMapping, eleitores: list[MembroId]) -> VotacaoOscar:
    return VotacaoOscar(
        id=VotacaoOscarId(UUID(linha["id"])),
        temporada_id=TemporadaOscarId(UUID(linha["temporada_id"])),
        eleitores=eleitores,
        iniciada_em=linha["iniciada_em"],
        turno_atual=linha["turno_atual"],
        encerrada_em=linha["encerrada_em"],
    )
