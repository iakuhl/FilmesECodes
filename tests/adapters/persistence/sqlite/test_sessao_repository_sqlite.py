"""Testes de integração de `SessaoRepositorioSqlite` contra um SQLite real."""

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
from filmes_e_cubos.adapters.persistence.sqlite.sessao_repository_sqlite import (
    SessaoRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao


def _indicacao_salva(engine: Engine) -> tuple[Indicacao, list[Membro]]:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    RodadaRepositorioSqlite(engine).salvar(rodada)
    membros_repo = MembroRepositorioSqlite(engine)
    membros = [
        Membro.criar(clube_id=clube.id, nome=nome, data_ingresso=date(2024, 1, 1))
        for nome in ("Ana", "Bia", "Caio")
    ]
    for membro in membros:
        membros_repo.salvar(membro)
    filme = Filme.criar(titulo="Duna")
    FilmeRepositorioSqlite(engine).salvar(filme)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id,
        membro_id=membros[0].id,
        filme_id=filme.id,
        data_indicacao=date(2024, 1, 2),
    )
    IndicacaoRepositorioSqlite(engine).salvar(indicacao)
    return indicacao, membros


def test_salvar_preserva_conjunto_de_presentes(engine: Engine) -> None:
    indicacao, membros = _indicacao_salva(engine)
    repositorio = SessaoRepositorioSqlite(engine)
    presentes = frozenset({membros[0].id, membros[2].id})
    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao.id, data_sessao=date(2024, 1, 7), membros_presentes=presentes
    )

    repositorio.salvar(sessao)
    recuperada = repositorio.buscar_por_id(sessao.id)

    assert recuperada is not None
    assert recuperada.membros_presentes == presentes
    assert repositorio.buscar_por_indicacao(indicacao.id) is not None


def test_salvar_novamente_substitui_o_conjunto_de_presentes(engine: Engine) -> None:
    indicacao, membros = _indicacao_salva(engine)
    repositorio = SessaoRepositorioSqlite(engine)
    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao.id,
        data_sessao=date(2024, 1, 7),
        membros_presentes=frozenset({membros[0].id}),
    )
    repositorio.salvar(sessao)

    sessao_atualizada = SessaoExibicao(
        id=sessao.id,
        indicacao_id=sessao.indicacao_id,
        data_sessao=sessao.data_sessao,
        membros_presentes=frozenset({membros[1].id, membros[2].id}),
    )
    repositorio.salvar(sessao_atualizada)

    recuperada = repositorio.buscar_por_id(sessao.id)
    assert recuperada is not None
    assert recuperada.membros_presentes == frozenset({membros[1].id, membros[2].id})


def test_sessao_sem_presentes_recupera_conjunto_vazio(engine: Engine) -> None:
    indicacao, _membros = _indicacao_salva(engine)
    repositorio = SessaoRepositorioSqlite(engine)
    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao.id, data_sessao=date(2024, 1, 7), membros_presentes=frozenset()
    )

    repositorio.salvar(sessao)
    recuperada = repositorio.buscar_por_id(sessao.id)

    assert recuperada is not None
    assert recuperada.membros_presentes == frozenset()
