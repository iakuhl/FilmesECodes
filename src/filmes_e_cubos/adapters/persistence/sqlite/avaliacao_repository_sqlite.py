"""Implementação SQLite (via SQLAlchemy Core) de `AvaliacaoRepository`."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import avaliacoes
from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.value_objects.identificadores import (
    AvaliacaoId,
    MembroId,
    SessaoExibicaoId,
)
from filmes_e_cubos.domain.value_objects.nota import Nota
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao


class AvaliacaoRepositorioSqlite:
    """Persiste avaliações em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, avaliacao: Avaliacao) -> None:
        upsert(self._engine, avaliacoes, _para_linha(avaliacao))

    def listar_por_sessao(self, sessao_id: SessaoExibicaoId) -> list[Avaliacao]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(avaliacoes.select().where(avaliacoes.c.sessao_id == str(sessao_id)))
                .mappings()
                .all()
            )
        return [_para_entidade(linha) for linha in linhas]

    def buscar_por_sessao_e_membro(
        self, sessao_id: SessaoExibicaoId, membro_id: MembroId
    ) -> Avaliacao | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(
                    avaliacoes.select().where(
                        avaliacoes.c.sessao_id == str(sessao_id),
                        avaliacoes.c.membro_id == str(membro_id),
                    )
                )
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None


def _para_linha(avaliacao: Avaliacao) -> dict[str, Any]:
    return {
        "id": str(avaliacao.id),
        "sessao_id": str(avaliacao.sessao_id),
        "membro_id": str(avaliacao.membro_id),
        "status": avaliacao.status.name,
        "nota": str(avaliacao.nota.valor) if avaliacao.nota is not None else None,
        "comentario": avaliacao.comentario,
    }


def _para_entidade(linha: RowMapping) -> Avaliacao:
    nota = Nota(Decimal(linha["nota"])) if linha["nota"] is not None else None
    return Avaliacao(
        id=AvaliacaoId(UUID(linha["id"])),
        sessao_id=SessaoExibicaoId(UUID(linha["sessao_id"])),
        membro_id=MembroId(UUID(linha["membro_id"])),
        status=StatusAvaliacao[linha["status"]],
        nota=nota,
        comentario=linha["comentario"],
    )
