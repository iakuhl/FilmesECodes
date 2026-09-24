"""Implementação SQLite (via SQLAlchemy Core) de `ClubeRepository`."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, RowMapping

from filmes_e_cubos.adapters.persistence.sqlite._upsert import upsert
from filmes_e_cubos.adapters.persistence.sqlite.esquema import clubes
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class ClubeRepositorioSqlite:
    """Persiste clubes em SQLite via SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def salvar(self, clube: Clube) -> None:
        upsert(self._engine, clubes, _para_linha(clube))

    def buscar_por_id(self, clube_id: ClubeId) -> Clube | None:
        with self._engine.connect() as conexao:
            linha = (
                conexao.execute(clubes.select().where(clubes.c.id == str(clube_id)))
                .mappings()
                .first()
            )
        return _para_entidade(linha) if linha is not None else None

    def listar_todos(self) -> list[Clube]:
        with self._engine.connect() as conexao:
            linhas = conexao.execute(clubes.select()).mappings().all()
        return [_para_entidade(linha) for linha in linhas]


def _para_linha(clube: Clube) -> dict[str, Any]:
    escala = clube.configuracao.escala_avaliacao
    return {
        "id": str(clube.id),
        "nome": clube.nome,
        "tamanho_rodada": clube.configuracao.tamanho_rodada,
        "nota_minima": str(escala.nota_minima),
        "nota_maxima": str(escala.nota_maxima),
        "passo": str(escala.passo),
    }


def _para_entidade(linha: RowMapping) -> Clube:
    escala = EscalaAvaliacao(
        nota_minima=Decimal(linha["nota_minima"]),
        nota_maxima=Decimal(linha["nota_maxima"]),
        passo=Decimal(linha["passo"]),
    )
    configuracao = ConfiguracaoClube(
        tamanho_rodada=linha["tamanho_rodada"], escala_avaliacao=escala
    )
    return Clube(id=ClubeId(UUID(linha["id"])), nome=linha["nome"], configuracao=configuracao)
