"""Testes do caso de uso EncerrarRodada."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.encerrar_rodada import EncerrarRodada
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.exceptions.rodada import RodadaNaoEncerravelError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId
from filmes_e_cubos.domain.value_objects.status import StatusRodada
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake


def test_encerrar_rodada_com_todas_as_indicacoes_assistidas(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    indicacoes = IndicacaoRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id,
        membro_id=MembroId(uuid4()),
        filme_id=FilmeId(uuid4()),
        data_indicacao=date(2024, 1, 1),
    )
    indicacao.marcar_sorteada()
    indicacao.marcar_assistida()
    indicacoes.salvar(indicacao)
    caso_de_uso = EncerrarRodada(rodadas, indicacoes, RelogioFake(datetime(2024, 3, 1)))

    rodada_encerrada = caso_de_uso.executar(rodada_id=rodada.id)

    assert rodada_encerrada.status is StatusRodada.ENCERRADA


def test_encerrar_rodada_com_indicacao_pendente_levanta_erro(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    indicacoes = IndicacaoRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id,
        membro_id=MembroId(uuid4()),
        filme_id=FilmeId(uuid4()),
        data_indicacao=date(2024, 1, 1),
    )
    indicacoes.salvar(indicacao)
    caso_de_uso = EncerrarRodada(rodadas, indicacoes, RelogioFake(datetime(2024, 3, 1)))

    with pytest.raises(RodadaNaoEncerravelError):
        caso_de_uso.executar(rodada_id=rodada.id)


def test_encerrar_rodada_sem_nenhuma_indicacao_levanta_erro(clube: Clube) -> None:
    rodadas = RodadaRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    caso_de_uso = EncerrarRodada(
        rodadas, IndicacaoRepositorioFake(), RelogioFake(datetime(2024, 3, 1))
    )

    with pytest.raises(RodadaNaoEncerravelError):
        caso_de_uso.executar(rodada_id=rodada.id)
