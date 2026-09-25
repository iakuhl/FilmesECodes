"""Testes da entidade VotacaoOscar: eleitores definidos e turnos."""

from datetime import datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.oscar import (
    MembroForaDaVotacaoError,
    TemporadaIncompletaError,
    VotacaoEncerradaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, TemporadaOscarId

INICIO = datetime(2024, 12, 1, 20, 0)
FIM = datetime(2024, 12, 8, 20, 0)
IANO, BIA = MembroId(uuid4()), MembroId(uuid4())


def _votacao() -> VotacaoOscar:
    return VotacaoOscar.iniciar(
        temporada_id=TemporadaOscarId(uuid4()), eleitores=[IANO, BIA], momento=INICIO
    )


def test_votacao_comeca_no_1o_turno_com_os_eleitores_dados() -> None:
    votacao = _votacao()

    assert votacao.eleitores == {IANO, BIA}
    assert votacao.turno_atual == 1
    assert votacao.iniciada_em == INICIO
    assert not votacao.encerrada


def test_votacao_sem_eleitores_nao_comeca() -> None:
    with pytest.raises(TemporadaIncompletaError):
        VotacaoOscar.iniciar(temporada_id=TemporadaOscarId(uuid4()), eleitores=[], momento=INICIO)


def test_so_os_eleitores_votam() -> None:
    votacao = _votacao()

    votacao.verificar_eleitor(IANO)
    with pytest.raises(MembroForaDaVotacaoError):
        votacao.verificar_eleitor(MembroId(uuid4()))


def test_pendentes_sao_os_eleitores_que_nao_confirmaram() -> None:
    votacao = _votacao()

    assert votacao.pendentes([IANO]) == {BIA}
    assert votacao.pendentes([IANO, BIA]) == frozenset()


def test_turno_seguinte_e_fim_da_votacao() -> None:
    votacao = _votacao()

    votacao.abrir_turno_seguinte()
    votacao.encerrar(FIM)

    assert votacao.turno_atual == 2
    assert votacao.encerrada_em == FIM
    with pytest.raises(VotacaoEncerradaError):
        votacao.verificar_aberta()
    with pytest.raises(VotacaoEncerradaError):
        votacao.abrir_turno_seguinte()
