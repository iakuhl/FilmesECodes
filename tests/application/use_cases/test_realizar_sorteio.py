"""Testes do caso de uso RealizarSorteio."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.realizar_sorteio import RealizarSorteio
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaEncerradaError
from filmes_e_cubos.domain.exceptions.sorteio import NenhumaIndicacaoElegivelError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake
from tests.application.fakes.sorteador_fake import SorteadorFake
from tests.application.fakes.sorteio_repositorio_fake import SorteioRepositorioFake


def _nova_indicacao_pendente(rodada_id: object) -> Indicacao:
    return Indicacao.criar(
        rodada_id=rodada_id,  # type: ignore[arg-type]
        membro_id=MembroId(uuid4()),
        filme_id=FilmeId(uuid4()),
        data_indicacao=date(2024, 1, 1),
    )


def test_realizar_sorteio_marca_indicacao_escolhida_como_sorteada(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    indicacoes = IndicacaoRepositorioFake()
    sorteios = SorteioRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    indicacao_1 = _nova_indicacao_pendente(rodada.id)
    indicacao_2 = _nova_indicacao_pendente(rodada.id)
    indicacoes.salvar(indicacao_1)
    indicacoes.salvar(indicacao_2)
    caso_de_uso = RealizarSorteio(
        indicacoes,
        rodadas,
        sorteios,
        SorteadorFake(escolha=indicacao_2.id),
        RelogioFake(datetime(2024, 1, 7)),
    )

    sorteio = caso_de_uso.executar(rodada_id=rodada.id)

    assert sorteio.indicacao_sorteada_id == indicacao_2.id
    assert indicacoes.buscar_por_id(indicacao_2.id).status is StatusIndicacao.SORTEADA  # type: ignore[union-attr]
    assert indicacoes.buscar_por_id(indicacao_1.id).status is StatusIndicacao.PENDENTE  # type: ignore[union-attr]


def test_realizar_sorteio_sem_indicacoes_pendentes_levanta_erro(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    caso_de_uso = RealizarSorteio(
        IndicacaoRepositorioFake(),
        rodadas,
        SorteioRepositorioFake(),
        SorteadorFake(),
        RelogioFake(datetime(2024, 1, 7)),
    )

    with pytest.raises(NenhumaIndicacaoElegivelError):
        caso_de_uso.executar(rodada_id=rodada.id)


def test_realizar_sorteio_em_rodada_encerrada_levanta_erro(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodada.encerrar(data_encerramento=date(2024, 1, 8))
    rodadas.salvar(rodada)
    caso_de_uso = RealizarSorteio(
        IndicacaoRepositorioFake(),
        rodadas,
        SorteioRepositorioFake(),
        SorteadorFake(),
        RelogioFake(datetime(2024, 1, 7)),
    )

    with pytest.raises(RodadaJaEncerradaError):
        caso_de_uso.executar(rodada_id=rodada.id)
