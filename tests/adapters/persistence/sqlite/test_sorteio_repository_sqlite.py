"""Testes de integração de `SorteioRepositorioSqlite` contra um SQLite real."""

from datetime import date, datetime

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
from filmes_e_cubos.adapters.persistence.sqlite.sorteio_repository_sqlite import (
    SorteioRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sorteio import Sorteio


def test_salvar_e_listar_por_rodada(engine: Engine) -> None:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    RodadaRepositorioSqlite(engine).salvar(rodada)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    MembroRepositorioSqlite(engine).salvar(membro)
    filme = Filme.criar(titulo="Duna")
    FilmeRepositorioSqlite(engine).salvar(filme)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id, data_indicacao=date(2024, 1, 2)
    )
    IndicacaoRepositorioSqlite(engine).salvar(indicacao)

    repositorio = SorteioRepositorioSqlite(engine)
    sorteio = Sorteio.registrar(
        rodada_id=rodada.id,
        indicacao_sorteada_id=indicacao.id,
        data_sorteio=datetime(2024, 1, 7, 20, 30),
        metodo="sorteio_aleatorio_uniforme",
    )

    repositorio.salvar(sorteio)
    recuperados = repositorio.listar_por_rodada(rodada.id)

    assert len(recuperados) == 1
    assert recuperados[0].indicacao_sorteada_id == indicacao.id
    assert recuperados[0].data_sorteio == datetime(2024, 1, 7, 20, 30)
    assert recuperados[0].metodo == "sorteio_aleatorio_uniforme"
