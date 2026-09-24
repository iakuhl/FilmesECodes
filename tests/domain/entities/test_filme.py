"""Testes da entidade Filme."""

import pytest

from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.exceptions.filme import TituloFilmeObrigatorioError


def test_criar_filme_com_titulo_valido() -> None:
    filme = Filme.criar(titulo="Duna", ano_lancamento=2021)

    assert filme.titulo == "Duna"
    assert filme.ano_lancamento == 2021


@pytest.mark.parametrize("titulo_invalido", ["", "   "])
def test_criar_filme_sem_titulo_levanta_erro(titulo_invalido: str) -> None:
    with pytest.raises(TituloFilmeObrigatorioError):
        Filme.criar(titulo=titulo_invalido)
