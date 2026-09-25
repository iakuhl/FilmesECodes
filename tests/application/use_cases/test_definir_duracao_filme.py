"""Testes do caso de uso DefinirDuracaoFilme."""

from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.definir_duracao_filme import DefinirDuracaoFilme
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.filme import DuracaoFilmeInvalidaError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId
from tests.application.fakes.filme_repositorio_fake import FilmeRepositorioFake


def test_grava_a_duracao_de_um_filme_cadastrado_sem_ela() -> None:
    filmes = FilmeRepositorioFake()
    filme = Filme.criar(titulo="Parasita")
    filmes.salvar(filme)

    DefinirDuracaoFilme(filmes).executar(filme_id=filme.id, duracao_minutos=132)

    assert filmes.buscar_por_id(filme.id).duracao_minutos == 132  # type: ignore[union-attr]


def test_duracao_invalida_nao_e_gravada() -> None:
    filmes = FilmeRepositorioFake()
    filme = Filme.criar(titulo="Parasita")
    filmes.salvar(filme)

    with pytest.raises(DuracaoFilmeInvalidaError):
        DefinirDuracaoFilme(filmes).executar(filme_id=filme.id, duracao_minutos=0)


def test_filme_inexistente_levanta_erro() -> None:
    with pytest.raises(EntidadeNaoEncontradaError):
        DefinirDuracaoFilme(FilmeRepositorioFake()).executar(
            filme_id=FilmeId(uuid4()), duracao_minutos=90
        )
