"""Testes de integração de `NomeacaoOscarRepositorioSqlite` contra um SQLite real."""

from datetime import date

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.categoria_oscar_repository_sqlite import (
    CategoriaOscarRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.filme_repository_sqlite import (
    FilmeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.membro_repository_sqlite import (
    MembroRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.nomeacao_oscar_repository_sqlite import (
    NomeacaoOscarRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.temporada_oscar_repository_sqlite import (
    TemporadaOscarRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


def _categoria_salva(engine: Engine) -> tuple[CategoriaOscar, Filme, Membro]:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    TemporadaOscarRepositorioSqlite(engine).salvar(temporada)
    categoria = CategoriaOscar.criar(
        temporada_id=temporada.id, nome="Melhor veículo", tipo=TipoCategoriaOscar.VARIAVEL
    )
    CategoriaOscarRepositorioSqlite(engine).salvar(categoria)
    filme = Filme.criar(titulo="Duna")
    FilmeRepositorioSqlite(engine).salvar(filme)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    MembroRepositorioSqlite(engine).salvar(membro)
    return categoria, filme, membro


def test_nomeacao_com_indicador_preserva_membro(engine: Engine) -> None:
    categoria, filme, membro = _categoria_salva(engine)
    repositorio = NomeacaoOscarRepositorioSqlite(engine)
    nomeacao = NomeacaoOscar.criar(
        categoria_id=categoria.id, filme_id=filme.id, indicado_por_membro_id=membro.id
    )

    repositorio.salvar(nomeacao)
    recuperada = repositorio.buscar_por_id(nomeacao.id)

    assert recuperada is not None
    assert recuperada.indicado_por_membro_id == membro.id


def test_nomeacao_democracia_preserva_indicador_nulo(engine: Engine) -> None:
    categoria, filme, _membro = _categoria_salva(engine)
    repositorio = NomeacaoOscarRepositorioSqlite(engine)
    nomeacao = NomeacaoOscar.criar(
        categoria_id=categoria.id, filme_id=filme.id, indicado_por_membro_id=None
    )

    repositorio.salvar(nomeacao)
    recuperada = repositorio.buscar_por_id(nomeacao.id)

    assert recuperada is not None
    assert recuperada.indicado_por_membro_id is None


def test_listar_por_categoria(engine: Engine) -> None:
    categoria, filme, membro = _categoria_salva(engine)
    repositorio = NomeacaoOscarRepositorioSqlite(engine)
    repositorio.salvar(
        NomeacaoOscar.criar(
            categoria_id=categoria.id, filme_id=filme.id, indicado_por_membro_id=membro.id
        )
    )

    assert len(repositorio.listar_por_categoria(categoria.id)) == 1
