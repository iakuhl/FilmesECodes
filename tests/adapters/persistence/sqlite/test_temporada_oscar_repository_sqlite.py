"""Testes de integração de `TemporadaOscarRepositorioSqlite` contra um SQLite real."""

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.temporada_oscar_repository_sqlite import (
    TemporadaOscarRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar


def test_salvar_e_buscar_por_clube_e_ano(engine: Engine) -> None:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    repositorio = TemporadaOscarRepositorioSqlite(engine)
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")

    repositorio.salvar(temporada)
    recuperada = repositorio.buscar_por_clube_e_ano(clube.id, 2024)

    assert recuperada is not None
    assert recuperada.id == temporada.id
    assert recuperada.status is StatusTemporadaOscar.EM_PREPARACAO


def test_salvar_apos_avancar_status_persiste_a_mudanca(engine: Engine) -> None:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    repositorio = TemporadaOscarRepositorioSqlite(engine)
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    repositorio.salvar(temporada)

    temporada.avancar_para(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)
    repositorio.salvar(temporada)

    recuperada = repositorio.buscar_por_id(temporada.id)
    assert recuperada is not None
    assert recuperada.status is StatusTemporadaOscar.ABERTA_PARA_INDICACOES


def test_listar_por_clube(engine: Engine) -> None:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    repositorio = TemporadaOscarRepositorioSqlite(engine)
    repositorio.salvar(TemporadaOscar.abrir(clube_id=clube.id, ano=2023, nome="Óscar 2023"))
    repositorio.salvar(TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024"))

    anos = {temporada.ano for temporada in repositorio.listar_por_clube(clube.id)}

    assert anos == {2023, 2024}
