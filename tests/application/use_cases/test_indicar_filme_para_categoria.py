"""Testes do caso de uso IndicarFilmeParaCategoria."""

from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.indicar_filme_para_categoria import (
    IndicarFilmeParaCategoria,
)
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    ClubeId,
    FilmeId,
    MembroId,
)
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.nomeacao_oscar_repositorio_fake import NomeacaoOscarRepositorioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake
from tests.application.fakes.sessao_repositorio_fake import SessaoRepositorioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)


@dataclass
class Cenario:
    """Uma categoria do Óscar de 2024 de um clube, e os repositórios em volta."""

    clube_id: ClubeId = field(default_factory=lambda: ClubeId(uuid4()))
    categorias: CategoriaOscarRepositorioFake = field(default_factory=CategoriaOscarRepositorioFake)
    temporadas: TemporadaOscarRepositorioFake = field(default_factory=TemporadaOscarRepositorioFake)
    indicacoes: IndicacaoRepositorioFake = field(default_factory=IndicacaoRepositorioFake)
    sessoes: SessaoRepositorioFake = field(default_factory=SessaoRepositorioFake)
    rodadas: RodadaRepositorioFake = field(default_factory=RodadaRepositorioFake)
    nomeacoes: NomeacaoOscarRepositorioFake = field(default_factory=NomeacaoOscarRepositorioFake)

    def __post_init__(self) -> None:
        temporada = TemporadaOscar.abrir(clube_id=self.clube_id, ano=2024, nome="Óscar 2024")
        self.temporadas.salvar(temporada)
        self.categoria = CategoriaOscar.criar(
            temporada_id=temporada.id, nome="Melhor veículo", tipo=TipoCategoriaOscar.VARIAVEL
        )
        self.categorias.salvar(self.categoria)
        self.caso_de_uso = IndicarFilmeParaCategoria(
            self.nomeacoes,
            self.categorias,
            self.temporadas,
            self.indicacoes,
            self.sessoes,
            self.rodadas,
        )

    def assistir(
        self,
        filme_id: FilmeId,
        data_sessao: date,
        membro_id: MembroId | None,
        *,
        clube_id: ClubeId | None = None,
    ) -> Indicacao:
        """Registra uma sessão do filme numa rodada do clube (ou de outro clube)."""
        rodada = Rodada.abrir(clube_id=clube_id or self.clube_id, numero=1, data_inicio=data_sessao)
        self.rodadas.salvar(rodada)
        if membro_id is None:
            indicacao = Indicacao.criar_democracia(
                rodada_id=rodada.id, filme_id=filme_id, data_indicacao=data_sessao
            )
        else:
            indicacao = Indicacao.criar(
                rodada_id=rodada.id,
                membro_id=membro_id,
                filme_id=filme_id,
                data_indicacao=data_sessao,
            )
        indicacao.marcar_assistida()
        self.indicacoes.salvar(indicacao)
        self.sessoes.salvar(
            SessaoExibicao.registrar(
                indicacao_id=indicacao.id, data_sessao=data_sessao, membros_presentes=frozenset()
            )
        )
        return indicacao


def test_indicar_filme_assistido_no_ano_da_temporada_herda_membro_indicador() -> None:
    cenario = Cenario()
    membro_id = MembroId(uuid4())
    filme_id = FilmeId(uuid4())
    cenario.assistir(filme_id, date(2024, 6, 1), membro_id)

    nomeacao = cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id, filme_id=filme_id)

    assert nomeacao.indicado_por_membro_id == membro_id


def test_indicar_filme_democracia_gera_nomeacao_sem_indicador() -> None:
    cenario = Cenario()
    filme_id = FilmeId(uuid4())
    cenario.assistir(filme_id, date(2024, 6, 1), membro_id=None)

    nomeacao = cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id, filme_id=filme_id)

    assert nomeacao.indicado_por_membro_id is None


def test_indicar_filme_assistido_em_outro_ano_levanta_erro() -> None:
    cenario = Cenario()
    filme_id = FilmeId(uuid4())
    cenario.assistir(filme_id, date(2023, 6, 1), MembroId(uuid4()))

    with pytest.raises(FilmeNaoAssistidoNoAnoDaTemporadaError):
        cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id, filme_id=filme_id)


def test_indicar_filme_nunca_assistido_para_categoria_levanta_erro() -> None:
    cenario = Cenario()

    with pytest.raises(FilmeNaoAssistidoError):
        cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id, filme_id=FilmeId(uuid4()))


def test_filme_assistido_so_por_outro_clube_nao_concorre() -> None:
    cenario = Cenario()
    filme_id = FilmeId(uuid4())
    cenario.assistir(filme_id, date(2024, 6, 1), MembroId(uuid4()), clube_id=ClubeId(uuid4()))

    with pytest.raises(FilmeNaoAssistidoError):
        cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id, filme_id=filme_id)


def test_indicar_filme_para_categoria_inexistente_levanta_erro() -> None:
    cenario = Cenario()

    with pytest.raises(EntidadeNaoEncontradaError):
        cenario.caso_de_uso.executar(
            categoria_id=CategoriaOscarId(uuid4()), filme_id=FilmeId(uuid4())
        )
