"""Testes da entidade Filme."""

import pytest

from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.exceptions.filme import (
    DuracaoFilmeInvalidaError,
    TituloFilmeObrigatorioError,
)


def test_criar_filme_com_titulo_valido() -> None:
    filme = Filme.criar(titulo="Duna", ano_lancamento=2021)

    assert filme.titulo == "Duna"
    assert filme.ano_lancamento == 2021


@pytest.mark.parametrize("titulo_invalido", ["", "   "])
def test_criar_filme_sem_titulo_levanta_erro(titulo_invalido: str) -> None:
    with pytest.raises(TituloFilmeObrigatorioError):
        Filme.criar(titulo=titulo_invalido)


def test_duracao_e_opcional_no_cadastro() -> None:
    assert Filme.criar(titulo="Duna").duracao_minutos is None
    assert Filme.criar(titulo="Duna", duracao_minutos=155).duracao_minutos == 155


@pytest.mark.parametrize("duracao_invalida", [0, -90])
def test_duracao_precisa_ser_positiva(duracao_invalida: int) -> None:
    with pytest.raises(DuracaoFilmeInvalidaError):
        Filme.criar(titulo="Duna", duracao_minutos=duracao_invalida)

    filme = Filme.criar(titulo="Duna")
    with pytest.raises(DuracaoFilmeInvalidaError):
        filme.definir_duracao(duracao_invalida)
    assert filme.duracao_minutos is None


def test_definir_duracao_de_filme_ja_cadastrado() -> None:
    filme = Filme.criar(titulo="Duna", duracao_minutos=150)

    filme.definir_duracao(155)

    assert filme.duracao_minutos == 155
