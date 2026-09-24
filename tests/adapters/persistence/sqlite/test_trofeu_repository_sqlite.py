"""Testes de integração de `TrofeuRepositorioSqlite` contra um SQLite real."""

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
from filmes_e_cubos.adapters.persistence.sqlite.trofeu_repository_sqlite import (
    TrofeuRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


def test_salvar_e_buscar_por_categoria(engine: Engine) -> None:
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
    nomeacao = NomeacaoOscar.criar(
        categoria_id=categoria.id, filme_id=filme.id, indicado_por_membro_id=membro.id
    )
    NomeacaoOscarRepositorioSqlite(engine).salvar(nomeacao)

    repositorio = TrofeuRepositorioSqlite(engine)
    trofeu = Trofeu.emitir(
        categoria_id=categoria.id,
        nomeacao_vencedora_id=nomeacao.id,
        membro_vencedor_id=membro.id,
        data_apuracao=date(2024, 12, 20),
    )

    repositorio.salvar(trofeu)
    recuperado = repositorio.buscar_por_categoria(categoria.id)

    assert recuperado is not None
    assert recuperado.membro_vencedor_id == membro.id
    assert recuperado.data_apuracao == date(2024, 12, 20)


def test_buscar_por_categoria_sem_trofeu_retorna_none(engine: Engine) -> None:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    TemporadaOscarRepositorioSqlite(engine).salvar(temporada)
    categoria = CategoriaOscar.criar(
        temporada_id=temporada.id, nome="Melhor veículo", tipo=TipoCategoriaOscar.VARIAVEL
    )
    CategoriaOscarRepositorioSqlite(engine).salvar(categoria)

    assert TrofeuRepositorioSqlite(engine).buscar_por_categoria(categoria.id) is None
