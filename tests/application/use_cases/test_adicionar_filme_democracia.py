"""Testes do caso de uso AdicionarFilmeDemocracia."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.adicionar_filme_democracia import (
    AdicionarFilmeDemocracia,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.indicacao import FilmeRepetidoNoClubeError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId
from filmes_e_cubos.domain.value_objects.tipo_indicacao import TipoIndicacao
from tests.application.fakes.filme_repositorio_fake import FilmeRepositorioFake
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake


def test_adicionar_filme_democracia_na_rodada_aberta(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    filmes = FilmeRepositorioFake()
    filme = Filme.criar(titulo="Arrival")
    filmes.salvar(filme)
    indicacoes = IndicacaoRepositorioFake()
    caso_de_uso = AdicionarFilmeDemocracia(
        indicacoes, rodadas, filmes, RelogioFake(datetime(2024, 1, 10))
    )

    indicacao = caso_de_uso.executar(clube_id=clube.id, filme_id=filme.id)

    assert indicacao.tipo is TipoIndicacao.DEMOCRACIA
    assert indicacao.membro_id is None
    assert indicacao.rodada_id == rodada.id


def test_adicionar_filme_democracia_sem_rodada_aberta_levanta_erro(clube: Clube) -> None:
    caso_de_uso = AdicionarFilmeDemocracia(
        IndicacaoRepositorioFake(),
        RodadaRepositorioFake(),
        FilmeRepositorioFake(),
        RelogioFake(datetime(2024, 1, 10)),
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(clube_id=clube.id, filme_id=FilmeId(uuid4()))


def test_adicionar_filme_democracia_com_filme_inexistente_levanta_erro(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    caso_de_uso = AdicionarFilmeDemocracia(
        IndicacaoRepositorioFake(),
        rodadas,
        FilmeRepositorioFake(),
        RelogioFake(datetime(2024, 1, 10)),
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(clube_id=clube.id, filme_id=FilmeId(uuid4()))


def test_democracia_tambem_nao_repete_filme_do_clube(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    filmes = FilmeRepositorioFake()
    filme = Filme.criar(titulo="Arrival")
    filmes.salvar(filme)
    indicacoes = IndicacaoRepositorioFake()
    indicacoes.salvar(
        Indicacao.criar(
            rodada_id=rodada.id,
            membro_id=MembroId(uuid4()),
            filme_id=filme.id,
            data_indicacao=date(2024, 1, 2),
        )
    )
    caso_de_uso = AdicionarFilmeDemocracia(
        indicacoes, rodadas, filmes, RelogioFake(datetime(2024, 1, 10))
    )

    with pytest.raises(FilmeRepetidoNoClubeError):
        caso_de_uso.executar(clube_id=clube.id, filme_id=filme.id)
