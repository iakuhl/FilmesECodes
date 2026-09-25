"""Testes de integração de `TurnoDeVotacaoRepositorioSqlite` contra um SQLite real."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.turno_de_votacao_repository_sqlite import (
    TurnoDeVotacaoRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, NomeacaoOscarId
from filmes_e_cubos.domain.value_objects.status import ModoDeVotacao

APURACAO = datetime(2024, 12, 8, 21, 0)


def test_turno_aberto_guarda_as_candidatas_em_ordem(engine: Engine) -> None:
    repositorio = TurnoDeVotacaoRepositorioSqlite(engine)
    candidatas = [NomeacaoOscarId(uuid4()) for _ in range(5)]
    turno = TurnoDeVotacao.abrir_primeiro(
        categoria_id=CategoriaOscarId(uuid4()), candidatas=candidatas
    )

    repositorio.salvar(turno)
    [encontrado] = repositorio.listar_por_categoria(turno.categoria_id)

    assert encontrado.id == turno.id
    assert encontrado.numero == 1
    assert encontrado.modo is ModoDeVotacao.DUPLA
    assert encontrado.candidatas == tuple(candidatas)
    assert encontrado.aberto
    assert encontrado.pontuacao is None


def test_apuracao_e_turno_seguinte_sao_guardados(engine: Engine) -> None:
    repositorio = TurnoDeVotacaoRepositorioSqlite(engine)
    a, b = NomeacaoOscarId(uuid4()), NomeacaoOscarId(uuid4())
    primeiro = TurnoDeVotacao.abrir_primeiro(
        categoria_id=CategoriaOscarId(uuid4()), candidatas=[a, b]
    )
    repositorio.salvar(primeiro)

    seguinte = primeiro.apurar([(a, b), (b, a)], momento=APURACAO)
    assert seguinte is not None
    repositorio.salvar(primeiro)
    repositorio.salvar(seguinte)

    apurado, desempate = repositorio.listar_por_categoria(primeiro.categoria_id)
    assert apurado.pontuacao == (3, 3)
    assert apurado.apurado_em == APURACAO
    assert not apurado.aberto
    assert desempate.numero == 2
    assert desempate.modo is ModoDeVotacao.CLASSIFICACAO
    assert desempate.aberto


def test_categoria_sem_turnos(engine: Engine) -> None:
    assert (
        TurnoDeVotacaoRepositorioSqlite(engine).listar_por_categoria(CategoriaOscarId(uuid4()))
        == []
    )
