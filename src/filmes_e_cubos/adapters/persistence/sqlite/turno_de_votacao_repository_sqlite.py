"""Implementação SQLite (via SQLAlchemy Core) de `TurnoDeVotacaoRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert_na_conexao
from filmes_e_cubos.adapters.persistence.sqlite.esquema import turno_candidatas, turnos_votacao
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    NomeacaoOscarId,
    TurnoDeVotacaoId,
)
from filmes_e_cubos.domain.value_objects.status import ModoDeVotacao


class TurnoDeVotacaoRepositorioSqlite:
    """Persiste os turnos de votação (candidatas e pontos, em ordem) em SQLite."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, turno: TurnoDeVotacao) -> None:
        pontuacao = turno.pontuacao or (None,) * len(turno.candidatas)
        with self._engine.begin() as conexao:
            upsert_na_conexao(conexao, turnos_votacao, _para_linha(turno))
            conexao.execute(
                turno_candidatas.delete().where(turno_candidatas.c.turno_id == str(turno.id))
            )
            conexao.execute(
                turno_candidatas.insert(),
                [
                    {
                        "turno_id": str(turno.id),
                        "posicao": posicao,
                        "nomeacao_id": str(nomeacao_id),
                        "pontos": pontos,
                    }
                    for posicao, (nomeacao_id, pontos) in enumerate(
                        zip(turno.candidatas, pontuacao, strict=True), start=1
                    )
                ],
            )

    def listar_por_categoria(self, categoria_id: CategoriaOscarId) -> list[TurnoDeVotacao]:
        with self._engine.connect() as conexao:
            linhas = (
                conexao.execute(
                    turnos_votacao.select()
                    .where(turnos_votacao.c.categoria_id == str(categoria_id))
                    .order_by(turnos_votacao.c.numero)
                )
                .mappings()
                .all()
            )
            return [_para_entidade(linha, _candidatas(conexao, linha["id"])) for linha in linhas]


def _candidatas(conexao: Connection, turno_id: str) -> list[RowMapping]:
    return list(
        conexao.execute(
            turno_candidatas.select()
            .where(turno_candidatas.c.turno_id == turno_id)
            .order_by(turno_candidatas.c.posicao)
        )
        .mappings()
        .all()
    )


def _para_linha(turno: TurnoDeVotacao) -> dict[str, Any]:
    return {
        "id": str(turno.id),
        "categoria_id": str(turno.categoria_id),
        "numero": turno.numero,
        "modo": turno.modo.name,
        "apurado_em": turno.apurado_em,
    }


def _para_entidade(linha: RowMapping, candidatas: list[RowMapping]) -> TurnoDeVotacao:
    apurado = linha["apurado_em"] is not None
    return TurnoDeVotacao(
        id=TurnoDeVotacaoId(UUID(linha["id"])),
        categoria_id=CategoriaOscarId(UUID(linha["categoria_id"])),
        numero=linha["numero"],
        modo=ModoDeVotacao[linha["modo"]],
        candidatas=[NomeacaoOscarId(UUID(candidata["nomeacao_id"])) for candidata in candidatas],
        pontuacao=[candidata["pontos"] for candidata in candidatas] if apurado else None,
        apurado_em=linha["apurado_em"],
    )
