"""Testes do caso de uso IndicarFilmeParaCategoria."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.indicar_filme_para_categoria import (
    IndicarFilmeParaCategoria,
)
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import FilmeNaoAssistidoError
from filmes_e_cubos.domain.value_objects.identificadores import (
    FilmeId,
    MembroId,
    RodadaId,
    TemporadaOscarId,
)
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.nomeacao_oscar_repositorio_fake import NomeacaoOscarRepositorioFake


def _preparar_categoria(categorias: CategoriaOscarRepositorioFake) -> CategoriaOscar:
    categoria = CategoriaOscar.criar(
        temporada_id=TemporadaOscarId(uuid4()),
        nome="Melhor veículo",
        tipo=TipoCategoriaOscar.VARIAVEL,
    )
    categorias.salvar(categoria)
    return categoria


def test_indicar_filme_assistido_para_categoria_herda_membro_indicador() -> None:
    categorias = CategoriaOscarRepositorioFake()
    categoria = _preparar_categoria(categorias)
    indicacoes = IndicacaoRepositorioFake()
    membro_id = MembroId(uuid4())
    filme_id = FilmeId(uuid4())
    indicacao = Indicacao.criar(
        rodada_id=RodadaId(uuid4()),
        membro_id=membro_id,
        filme_id=filme_id,
        data_indicacao=date(2024, 1, 1),
    )
    indicacao.marcar_sorteada()
    indicacao.marcar_assistida()
    indicacoes.salvar(indicacao)
    nomeacoes = NomeacaoOscarRepositorioFake()
    caso_de_uso = IndicarFilmeParaCategoria(nomeacoes, categorias, indicacoes)

    nomeacao = caso_de_uso.executar(categoria_id=categoria.id, filme_id=filme_id)

    assert nomeacao.indicado_por_membro_id == membro_id


def test_indicar_filme_nunca_assistido_para_categoria_levanta_erro() -> None:
    categorias = CategoriaOscarRepositorioFake()
    categoria = _preparar_categoria(categorias)
    caso_de_uso = IndicarFilmeParaCategoria(
        NomeacaoOscarRepositorioFake(), categorias, IndicacaoRepositorioFake()
    )

    with pytest.raises(FilmeNaoAssistidoError):
        caso_de_uso.executar(categoria_id=categoria.id, filme_id=FilmeId(uuid4()))


def test_indicar_filme_para_categoria_inexistente_levanta_erro() -> None:
    caso_de_uso = IndicarFilmeParaCategoria(
        NomeacaoOscarRepositorioFake(), CategoriaOscarRepositorioFake(), IndicacaoRepositorioFake()
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(categoria_id=uuid4(), filme_id=FilmeId(uuid4()))  # type: ignore[arg-type]
