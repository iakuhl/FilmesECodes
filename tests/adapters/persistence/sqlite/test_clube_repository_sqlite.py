"""Testes de integração de `ClubeRepositorioSqlite` contra um SQLite real."""

from decimal import Decimal

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao


def test_salvar_e_buscar_por_id_preserva_configuracao_com_precisao_decimal(engine: Engine) -> None:
    repositorio = ClubeRepositorioSqlite(engine)
    clube = Clube.criar(
        nome="Filmes e Cubos",
        configuracao=ConfiguracaoClube(
            tamanho_rodada=5,
            escala_avaliacao=EscalaAvaliacao(
                nota_minima=Decimal("0.5"), nota_maxima=Decimal("5.0"), passo=Decimal("0.5")
            ),
        ),
    )

    repositorio.salvar(clube)
    recuperado = repositorio.buscar_por_id(clube.id)

    assert recuperado is not None
    assert recuperado.id == clube.id
    assert recuperado.nome == "Filmes e Cubos"
    assert recuperado.configuracao.tamanho_rodada == 5
    assert recuperado.configuracao.escala_avaliacao.nota_minima == Decimal("0.5")
    assert recuperado.configuracao.escala_avaliacao.passo == Decimal("0.5")


def test_buscar_por_id_inexistente_retorna_none(engine: Engine) -> None:
    repositorio = ClubeRepositorioSqlite(engine)

    assert repositorio.buscar_por_id(Clube.criar(nome="X").id) is None


def test_salvar_duas_vezes_atualiza_em_vez_de_duplicar(engine: Engine) -> None:
    repositorio = ClubeRepositorioSqlite(engine)
    clube = Clube.criar(nome="Filmes e Cubos")
    repositorio.salvar(clube)

    clube.atualizar_configuracao(
        ConfiguracaoClube(tamanho_rodada=7, escala_avaliacao=clube.configuracao.escala_avaliacao)
    )
    repositorio.salvar(clube)

    assert len(repositorio.listar_todos()) == 1
    recuperado = repositorio.buscar_por_id(clube.id)
    assert recuperado is not None
    assert recuperado.configuracao.tamanho_rodada == 7


def test_listar_todos_retorna_todos_os_clubes_salvos(engine: Engine) -> None:
    repositorio = ClubeRepositorioSqlite(engine)
    repositorio.salvar(Clube.criar(nome="Filmes e Cubos"))
    repositorio.salvar(Clube.criar(nome="Outro Clube"))

    nomes = {clube.nome for clube in repositorio.listar_todos()}

    assert nomes == {"Filmes e Cubos", "Outro Clube"}
