"""Testes de integração de `IndicacaoRepositorioSqlite` contra um SQLite real."""

from datetime import date

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.filme_repository_sqlite import (
    FilmeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.indicacao_repository_sqlite import (
    IndicacaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.membro_repository_sqlite import (
    MembroRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.rodada_repository_sqlite import (
    RodadaRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao
from filmes_e_cubos.domain.value_objects.tipo_indicacao import TipoIndicacao


def _preparar(engine: Engine) -> tuple[Rodada, Membro, Filme]:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    RodadaRepositorioSqlite(engine).salvar(rodada)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    MembroRepositorioSqlite(engine).salvar(membro)
    filme = Filme.criar(titulo="Duna")
    FilmeRepositorioSqlite(engine).salvar(filme)
    return rodada, membro, filme


def test_indicacao_normal_preserva_membro_e_tipo(engine: Engine) -> None:
    rodada, membro, filme = _preparar(engine)
    repositorio = IndicacaoRepositorioSqlite(engine)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id, data_indicacao=date(2024, 1, 2)
    )

    repositorio.salvar(indicacao)
    recuperada = repositorio.buscar_por_id(indicacao.id)

    assert recuperada is not None
    assert recuperada.tipo is TipoIndicacao.NORMAL
    assert recuperada.membro_id == membro.id
    assert recuperada.status is StatusIndicacao.PENDENTE


def test_indicacao_democracia_preserva_membro_nulo(engine: Engine) -> None:
    rodada, _membro, filme = _preparar(engine)
    repositorio = IndicacaoRepositorioSqlite(engine)
    indicacao = Indicacao.criar_democracia(
        rodada_id=rodada.id, filme_id=filme.id, data_indicacao=date(2024, 1, 2)
    )

    repositorio.salvar(indicacao)
    recuperada = repositorio.buscar_por_id(indicacao.id)

    assert recuperada is not None
    assert recuperada.tipo is TipoIndicacao.DEMOCRACIA
    assert recuperada.membro_id is None


def test_salvar_apos_transicao_de_status_persiste_a_mudanca(engine: Engine) -> None:
    rodada, membro, filme = _preparar(engine)
    repositorio = IndicacaoRepositorioSqlite(engine)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id, data_indicacao=date(2024, 1, 2)
    )
    repositorio.salvar(indicacao)

    indicacao.marcar_assistida()
    repositorio.salvar(indicacao)

    recuperada = repositorio.buscar_por_id(indicacao.id)
    assert recuperada is not None
    assert recuperada.status is StatusIndicacao.ASSISTIDA


def test_listar_por_rodada_e_listar_assistidas_por_filme(engine: Engine) -> None:
    rodada, membro, filme = _preparar(engine)
    repositorio = IndicacaoRepositorioSqlite(engine)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id, data_indicacao=date(2024, 1, 2)
    )
    indicacao.marcar_assistida()
    repositorio.salvar(indicacao)

    assert [i.id for i in repositorio.listar_por_rodada(rodada.id)] == [indicacao.id]
    assert [i.id for i in repositorio.listar_assistidas_por_filme(filme.id)] == [indicacao.id]


def test_listar_por_filme_traz_indicacoes_em_qualquer_situacao(engine: Engine) -> None:
    rodada, membro, filme = _preparar(engine)
    repositorio = IndicacaoRepositorioSqlite(engine)
    pendente = Indicacao.criar(
        rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id, data_indicacao=date(2024, 1, 2)
    )
    assistida = Indicacao.criar_democracia(
        rodada_id=rodada.id, filme_id=filme.id, data_indicacao=date(2024, 1, 3)
    )
    assistida.marcar_assistida()
    repositorio.salvar(pendente)
    repositorio.salvar(assistida)

    encontradas = repositorio.listar_por_filme(filme.id)

    assert {indicacao.id for indicacao in encontradas} == {pendente.id, assistida.id}
