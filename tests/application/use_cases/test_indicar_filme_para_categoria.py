"""Testes do caso de uso IndicarFilmeParaCategoria."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.indicar_filme_para_categoria import (
    IndicarFilmeParaCategoria,
)
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    ClubeId,
    FilmeId,
    MembroId,
    RodadaId,
)
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.nomeacao_oscar_repositorio_fake import NomeacaoOscarRepositorioFake
from tests.application.fakes.sessao_repositorio_fake import SessaoRepositorioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)


def _preparar_categoria(
    categorias: CategoriaOscarRepositorioFake, temporadas: TemporadaOscarRepositorioFake, ano: int
) -> CategoriaOscar:
    temporada = TemporadaOscar.abrir(clube_id=ClubeId(uuid4()), ano=ano, nome=f"Óscar {ano}")
    temporadas.salvar(temporada)
    categoria = CategoriaOscar.criar(
        temporada_id=temporada.id, nome="Melhor veículo", tipo=TipoCategoriaOscar.VARIAVEL
    )
    categorias.salvar(categoria)
    return categoria


def _assistir_filme(
    indicacoes: IndicacaoRepositorioFake,
    sessoes: SessaoRepositorioFake,
    filme_id: FilmeId,
    data_sessao: date,
    membro_id: MembroId | None,
) -> Indicacao:
    if membro_id is None:
        indicacao = Indicacao.criar_democracia(
            rodada_id=RodadaId(uuid4()), filme_id=filme_id, data_indicacao=data_sessao
        )
    else:
        indicacao = Indicacao.criar(
            rodada_id=RodadaId(uuid4()),
            membro_id=membro_id,
            filme_id=filme_id,
            data_indicacao=data_sessao,
        )
    indicacao.marcar_assistida()
    indicacoes.salvar(indicacao)
    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao.id, data_sessao=data_sessao, membros_presentes=frozenset()
    )
    sessoes.salvar(sessao)
    return indicacao


def test_indicar_filme_assistido_no_ano_da_temporada_herda_membro_indicador() -> None:
    categorias = CategoriaOscarRepositorioFake()
    temporadas = TemporadaOscarRepositorioFake()
    categoria = _preparar_categoria(categorias, temporadas, ano=2024)
    indicacoes = IndicacaoRepositorioFake()
    sessoes = SessaoRepositorioFake()
    membro_id = MembroId(uuid4())
    filme_id = FilmeId(uuid4())
    _assistir_filme(indicacoes, sessoes, filme_id, date(2024, 6, 1), membro_id)
    nomeacoes = NomeacaoOscarRepositorioFake()
    caso_de_uso = IndicarFilmeParaCategoria(nomeacoes, categorias, temporadas, indicacoes, sessoes)

    nomeacao = caso_de_uso.executar(categoria_id=categoria.id, filme_id=filme_id)

    assert nomeacao.indicado_por_membro_id == membro_id


def test_indicar_filme_democracia_gera_nomeacao_sem_indicador() -> None:
    categorias = CategoriaOscarRepositorioFake()
    temporadas = TemporadaOscarRepositorioFake()
    categoria = _preparar_categoria(categorias, temporadas, ano=2024)
    indicacoes = IndicacaoRepositorioFake()
    sessoes = SessaoRepositorioFake()
    filme_id = FilmeId(uuid4())
    _assistir_filme(indicacoes, sessoes, filme_id, date(2024, 6, 1), membro_id=None)
    nomeacoes = NomeacaoOscarRepositorioFake()
    caso_de_uso = IndicarFilmeParaCategoria(nomeacoes, categorias, temporadas, indicacoes, sessoes)

    nomeacao = caso_de_uso.executar(categoria_id=categoria.id, filme_id=filme_id)

    assert nomeacao.indicado_por_membro_id is None


def test_indicar_filme_assistido_em_outro_ano_levanta_erro() -> None:
    categorias = CategoriaOscarRepositorioFake()
    temporadas = TemporadaOscarRepositorioFake()
    categoria = _preparar_categoria(categorias, temporadas, ano=2024)
    indicacoes = IndicacaoRepositorioFake()
    sessoes = SessaoRepositorioFake()
    filme_id = FilmeId(uuid4())
    _assistir_filme(indicacoes, sessoes, filme_id, date(2023, 6, 1), MembroId(uuid4()))
    caso_de_uso = IndicarFilmeParaCategoria(
        NomeacaoOscarRepositorioFake(), categorias, temporadas, indicacoes, sessoes
    )

    with pytest.raises(FilmeNaoAssistidoNoAnoDaTemporadaError):
        caso_de_uso.executar(categoria_id=categoria.id, filme_id=filme_id)


def test_indicar_filme_nunca_assistido_para_categoria_levanta_erro() -> None:
    categorias = CategoriaOscarRepositorioFake()
    temporadas = TemporadaOscarRepositorioFake()
    categoria = _preparar_categoria(categorias, temporadas, ano=2024)
    caso_de_uso = IndicarFilmeParaCategoria(
        NomeacaoOscarRepositorioFake(),
        categorias,
        temporadas,
        IndicacaoRepositorioFake(),
        SessaoRepositorioFake(),
    )

    with pytest.raises(FilmeNaoAssistidoError):
        caso_de_uso.executar(categoria_id=categoria.id, filme_id=FilmeId(uuid4()))


def test_indicar_filme_para_categoria_inexistente_levanta_erro() -> None:
    caso_de_uso = IndicarFilmeParaCategoria(
        NomeacaoOscarRepositorioFake(),
        CategoriaOscarRepositorioFake(),
        TemporadaOscarRepositorioFake(),
        IndicacaoRepositorioFake(),
        SessaoRepositorioFake(),
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(categoria_id=uuid4(), filme_id=FilmeId(uuid4()))  # type: ignore[arg-type]
