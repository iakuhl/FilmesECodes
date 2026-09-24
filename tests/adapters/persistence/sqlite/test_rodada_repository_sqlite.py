"""Testes de integração de `RodadaRepositorioSqlite` contra um SQLite real."""

from datetime import date

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.rodada_repository_sqlite import (
    RodadaRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.value_objects.status import StatusRodada


def _clube_salvo(engine: Engine) -> Clube:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    return clube


def test_salvar_e_buscar_aberta_por_clube(engine: Engine) -> None:
    clube = _clube_salvo(engine)
    repositorio = RodadaRepositorioSqlite(engine)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))

    repositorio.salvar(rodada)
    aberta = repositorio.buscar_aberta_por_clube(clube.id)

    assert aberta is not None
    assert aberta.id == rodada.id
    assert aberta.status is StatusRodada.ABERTA


def test_rodada_encerrada_nao_aparece_como_aberta(engine: Engine) -> None:
    clube = _clube_salvo(engine)
    repositorio = RodadaRepositorioSqlite(engine)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodada.encerrar(data_encerramento=date(2024, 3, 1))
    repositorio.salvar(rodada)

    assert repositorio.buscar_aberta_por_clube(clube.id) is None
    recuperada = repositorio.buscar_por_id(rodada.id)
    assert recuperada is not None
    assert recuperada.status is StatusRodada.ENCERRADA
    assert recuperada.data_encerramento == date(2024, 3, 1)


def test_contar_por_clube(engine: Engine) -> None:
    clube = _clube_salvo(engine)
    repositorio = RodadaRepositorioSqlite(engine)
    primeira = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    primeira.encerrar(data_encerramento=date(2024, 2, 1))
    repositorio.salvar(primeira)
    repositorio.salvar(Rodada.abrir(clube_id=clube.id, numero=2, data_inicio=date(2024, 2, 1)))

    assert repositorio.contar_por_clube(clube.id) == 2


def test_listar_por_clube_ordena_pelo_numero_e_isola_clubes(engine: Engine) -> None:
    clube = _clube_salvo(engine)
    outro_clube = _clube_salvo(engine)
    repositorio = RodadaRepositorioSqlite(engine)
    segunda = Rodada.abrir(clube_id=clube.id, numero=2, data_inicio=date(2024, 2, 1))
    primeira = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    primeira.encerrar(data_encerramento=date(2024, 2, 1))
    de_outro_clube = Rodada.abrir(clube_id=outro_clube.id, numero=1, data_inicio=date(2024, 1, 1))
    for rodada in (segunda, primeira, de_outro_clube):  # salvas fora de ordem de propósito
        repositorio.salvar(rodada)

    assert [rodada.id for rodada in repositorio.listar_por_clube(clube.id)] == [
        primeira.id,
        segunda.id,
    ]
