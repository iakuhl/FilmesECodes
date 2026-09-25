"""Testes de integração de `VotacaoOscarRepositorioSqlite` contra um SQLite real."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.votacao_oscar_repository_sqlite import (
    VotacaoOscarRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, TemporadaOscarId

INICIO = datetime(2024, 12, 1, 20, 0, 30)


def test_salvar_e_buscar_por_temporada(engine: Engine) -> None:
    repositorio = VotacaoOscarRepositorioSqlite(engine)
    eleitores = {MembroId(uuid4()), MembroId(uuid4())}
    votacao = VotacaoOscar.iniciar(
        temporada_id=TemporadaOscarId(uuid4()), eleitores=eleitores, momento=INICIO
    )

    repositorio.salvar(votacao)
    encontrada = repositorio.buscar_por_temporada(votacao.temporada_id)

    assert encontrada is not None
    assert encontrada.id == votacao.id
    assert encontrada.eleitores == eleitores
    assert encontrada.iniciada_em == INICIO
    assert encontrada.turno_atual == 1
    assert encontrada.encerrada_em is None


def test_salvar_de_novo_grava_o_turno_e_o_fim(engine: Engine) -> None:
    repositorio = VotacaoOscarRepositorioSqlite(engine)
    votacao = VotacaoOscar.iniciar(
        temporada_id=TemporadaOscarId(uuid4()), eleitores=[MembroId(uuid4())], momento=INICIO
    )
    repositorio.salvar(votacao)

    votacao.abrir_turno_seguinte()
    votacao.encerrar(datetime(2024, 12, 8, 22, 15))
    repositorio.salvar(votacao)

    encontrada = repositorio.buscar_por_temporada(votacao.temporada_id)
    assert encontrada is not None
    assert encontrada.turno_atual == 2
    assert encontrada.encerrada_em == datetime(2024, 12, 8, 22, 15)
    assert len(encontrada.eleitores) == 1


def test_temporada_sem_votacao(engine: Engine) -> None:
    assert (
        VotacaoOscarRepositorioSqlite(engine).buscar_por_temporada(TemporadaOscarId(uuid4()))
        is None
    )
