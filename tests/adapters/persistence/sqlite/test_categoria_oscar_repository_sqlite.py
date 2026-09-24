"""Testes de integração de `CategoriaOscarRepositorioSqlite` contra um SQLite real."""

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.categoria_oscar_repository_sqlite import (
    CategoriaOscarRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.temporada_oscar_repository_sqlite import (
    TemporadaOscarRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


def _temporada_salva(engine: Engine) -> TemporadaOscar:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    TemporadaOscarRepositorioSqlite(engine).salvar(temporada)
    return temporada


def test_salvar_e_buscar_por_id_preserva_tipo_e_descricao(engine: Engine) -> None:
    temporada = _temporada_salva(engine)
    repositorio = CategoriaOscarRepositorioSqlite(engine)
    categoria = CategoriaOscar.criar(
        temporada_id=temporada.id,
        nome="Melhor veículo",
        tipo=TipoCategoriaOscar.VARIAVEL,
        descricao="O carro mais icônico do ano",
    )

    repositorio.salvar(categoria)
    recuperada = repositorio.buscar_por_id(categoria.id)

    assert recuperada is not None
    assert recuperada.tipo is TipoCategoriaOscar.VARIAVEL
    assert recuperada.descricao == "O carro mais icônico do ano"


def test_listar_por_temporada(engine: Engine) -> None:
    temporada = _temporada_salva(engine)
    repositorio = CategoriaOscarRepositorioSqlite(engine)
    repositorio.salvar(
        CategoriaOscar.criar(
            temporada_id=temporada.id, nome="Melhor filme", tipo=TipoCategoriaOscar.FIXA
        )
    )
    repositorio.salvar(
        CategoriaOscar.criar(
            temporada_id=temporada.id, nome="Pior criança", tipo=TipoCategoriaOscar.VARIAVEL
        )
    )

    nomes = {categoria.nome for categoria in repositorio.listar_por_temporada(temporada.id)}

    assert nomes == {"Melhor filme", "Pior criança"}
