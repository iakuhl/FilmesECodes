"""Implementação SQLite (via SQLAlchemy Core) de `CedulaRepository`."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, Connection, Engine, RowMapping, and_

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert_na_conexao
from filmes_e_cubos.adapters.persistence.sqlite.esquema import cedula_escolhas, cedulas
from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    CedulaId,
    MembroId,
    NomeacaoOscarId,
    VotacaoOscarId,
)


class CedulaRepositorioSqlite:
    """Persiste as cédulas da votação (e as escolhas, em ordem) em SQLite."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, cedula: Cedula) -> None:
        linhas_das_escolhas = [
            {
                "cedula_id": str(cedula.id),
                "categoria_id": str(categoria_id),
                "posicao": posicao,
                "nomeacao_id": str(nomeacao_id),
            }
            for categoria_id, escolhidas in cedula.escolhas.items()
            for posicao, nomeacao_id in enumerate(escolhidas, start=1)
        ]
        with self._engine.begin() as conexao:
            upsert_na_conexao(conexao, cedulas, _para_linha(cedula))
            conexao.execute(
                cedula_escolhas.delete().where(cedula_escolhas.c.cedula_id == str(cedula.id))
            )
            if linhas_das_escolhas:
                conexao.execute(cedula_escolhas.insert(), linhas_das_escolhas)

    def buscar(self, votacao_id: VotacaoOscarId, turno: int, membro_id: MembroId) -> Cedula | None:
        encontradas = self._listar(
            and_(
                cedulas.c.votacao_id == str(votacao_id),
                cedulas.c.turno == turno,
                cedulas.c.membro_id == str(membro_id),
            )
        )
        return encontradas[0] if encontradas else None

    def listar_por_turno(self, votacao_id: VotacaoOscarId, turno: int) -> list[Cedula]:
        return self._listar(and_(cedulas.c.votacao_id == str(votacao_id), cedulas.c.turno == turno))

    def _listar(self, condicao: ColumnElement[bool]) -> list[Cedula]:
        with self._engine.connect() as conexao:
            linhas = conexao.execute(cedulas.select().where(condicao)).mappings().all()
            return [_para_entidade(linha, _escolhas(conexao, linha["id"])) for linha in linhas]


def _escolhas(conexao: Connection, cedula_id: str) -> dict[CategoriaOscarId, list[NomeacaoOscarId]]:
    escolhas: dict[CategoriaOscarId, list[NomeacaoOscarId]] = {}
    for linha in conexao.execute(
        cedula_escolhas.select()
        .where(cedula_escolhas.c.cedula_id == cedula_id)
        .order_by(cedula_escolhas.c.categoria_id, cedula_escolhas.c.posicao)
    ).mappings():
        escolhas.setdefault(CategoriaOscarId(UUID(linha["categoria_id"])), []).append(
            NomeacaoOscarId(UUID(linha["nomeacao_id"]))
        )
    return escolhas


def _para_linha(cedula: Cedula) -> dict[str, Any]:
    return {
        "id": str(cedula.id),
        "votacao_id": str(cedula.votacao_id),
        "turno": cedula.turno,
        "membro_id": str(cedula.membro_id),
        "confirmada_em": cedula.confirmada_em,
    }


def _para_entidade(
    linha: RowMapping, escolhas: dict[CategoriaOscarId, list[NomeacaoOscarId]]
) -> Cedula:
    return Cedula(
        id=CedulaId(UUID(linha["id"])),
        votacao_id=VotacaoOscarId(UUID(linha["votacao_id"])),
        turno=linha["turno"],
        membro_id=MembroId(UUID(linha["membro_id"])),
        escolhas=escolhas,
        confirmada_em=linha["confirmada_em"],
    )
