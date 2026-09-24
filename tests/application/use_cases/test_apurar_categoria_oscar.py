"""Testes do caso de uso ApurarCategoriaOscar."""

from datetime import datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.apurar_categoria_oscar import ApurarCategoriaOscar
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import CategoriaJaApuradaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    TemporadaOscarId,
)
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.criterio_apuracao_fake import CriterioApuracaoFake
from tests.application.fakes.nomeacao_oscar_repositorio_fake import NomeacaoOscarRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.trofeu_repositorio_fake import TrofeuRepositorioFake


def test_apurar_categoria_emite_trofeu_para_membro_da_nomeacao_vencedora() -> None:
    categorias = CategoriaOscarRepositorioFake()
    categoria = CategoriaOscar.criar(
        temporada_id=TemporadaOscarId(uuid4()),
        nome="Melhor veículo",
        tipo=TipoCategoriaOscar.VARIAVEL,
    )
    categorias.salvar(categoria)
    nomeacoes = NomeacaoOscarRepositorioFake()
    membro_vencedor_id = MembroId(uuid4())
    nomeacao_vencedora = NomeacaoOscar.criar(
        categoria_id=categoria.id,
        filme_id=FilmeId(uuid4()),
        indicado_por_membro_id=membro_vencedor_id,
    )
    nomeacoes.salvar(nomeacao_vencedora)
    trofeus = TrofeuRepositorioFake()
    caso_de_uso = ApurarCategoriaOscar(
        trofeus,
        nomeacoes,
        categorias,
        CriterioApuracaoFake(vencedora_id=nomeacao_vencedora.id),
        RelogioFake(datetime(2024, 12, 20)),
    )

    trofeu = caso_de_uso.executar(categoria_id=categoria.id)

    assert trofeu.membro_vencedor_id == membro_vencedor_id
    assert trofeus.buscar_por_categoria(categoria.id) is trofeu


def test_apurar_categoria_ja_apurada_levanta_erro() -> None:
    categorias = CategoriaOscarRepositorioFake()
    categoria = CategoriaOscar.criar(
        temporada_id=TemporadaOscarId(uuid4()),
        nome="Melhor veículo",
        tipo=TipoCategoriaOscar.VARIAVEL,
    )
    categorias.salvar(categoria)
    nomeacoes = NomeacaoOscarRepositorioFake()
    nomeacao = NomeacaoOscar.criar(
        categoria_id=categoria.id,
        filme_id=FilmeId(uuid4()),
        indicado_por_membro_id=MembroId(uuid4()),
    )
    nomeacoes.salvar(nomeacao)
    caso_de_uso = ApurarCategoriaOscar(
        TrofeuRepositorioFake(),
        nomeacoes,
        categorias,
        CriterioApuracaoFake(),
        RelogioFake(datetime(2024, 12, 20)),
    )
    caso_de_uso.executar(categoria_id=categoria.id)

    with pytest.raises(CategoriaJaApuradaError):
        caso_de_uso.executar(categoria_id=categoria.id)


def test_apurar_categoria_inexistente_levanta_erro() -> None:
    caso_de_uso = ApurarCategoriaOscar(
        TrofeuRepositorioFake(),
        NomeacaoOscarRepositorioFake(),
        CategoriaOscarRepositorioFake(),
        CriterioApuracaoFake(),
        RelogioFake(datetime(2024, 12, 20)),
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(categoria_id=CategoriaOscarId(uuid4()))
