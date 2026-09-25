"""Testes do caso de uso ConfirmarCedula: confirmação, fim do turno e desempates."""

from uuid import uuid4

import pytest

from filmes_e_cubos.domain.exceptions.oscar import (
    CedulaConfirmadaError,
    CedulaIncompletaError,
    MembroForaDaVotacaoError,
    VotacaoEncerradaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import MembroId
from filmes_e_cubos.domain.value_objects.status import ModoDeVotacao
from tests.application.use_cases.cenario_de_votacao import AGORA, CenarioDeVotacao


def test_confirmar_exige_voto_em_todas_as_categorias_do_turno() -> None:
    cenario = CenarioDeVotacao()
    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)

    with pytest.raises(CedulaIncompletaError, match="Falta votar em: Pior criança"):
        cenario.confirmar(cenario.iano)


def test_confirmar_sem_ter_votado_lista_todas_as_categorias() -> None:
    cenario = CenarioDeVotacao()

    with pytest.raises(CedulaIncompletaError, match="Melhor veículo, Pior criança"):
        cenario.confirmar(cenario.iano)


def test_primeira_confirmacao_nao_encerra_o_turno() -> None:
    cenario = CenarioDeVotacao()
    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)
    cenario.votar(cenario.iano, cenario.crianca, 0, 1)

    resultado = cenario.confirmar(cenario.iano)

    assert not resultado.turno_encerrado
    assert resultado.pendentes == {cenario.bia}
    cedula = cenario.cedulas.buscar(cenario.votacao.id, 1, cenario.iano)
    assert cedula is not None
    assert cedula.confirmada_em == AGORA
    assert cenario.veiculo.aberto


def test_confirmar_duas_vezes_e_recusado() -> None:
    cenario = CenarioDeVotacao()
    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)
    cenario.votar(cenario.iano, cenario.crianca, 0, 1)
    cenario.confirmar(cenario.iano)

    with pytest.raises(CedulaConfirmadaError):
        cenario.confirmar(cenario.iano)


def test_quem_nao_e_eleitor_nao_confirma() -> None:
    cenario = CenarioDeVotacao()

    with pytest.raises(MembroForaDaVotacaoError):
        cenario.confirmar(MembroId(uuid4()))


def test_ultima_confirmacao_apura_o_turno_e_termina_a_votacao() -> None:
    cenario = CenarioDeVotacao()
    for eleitor in (cenario.iano, cenario.bia):
        cenario.votar(eleitor, cenario.veiculo, 0, 1)
        cenario.votar(eleitor, cenario.crianca, 1, 0)
    cenario.confirmar(cenario.iano)

    resultado = cenario.confirmar(cenario.bia)

    assert resultado.turno_encerrado
    assert resultado.pendentes == frozenset()
    assert resultado.votacao.encerrada_em == AGORA
    assert cenario.veiculo.pontuacao == (4, 2)
    assert cenario.crianca.pontuacao == (2, 4)
    assert cenario.turno_aberto(cenario.veiculo) is None
    with pytest.raises(VotacaoEncerradaError):
        cenario.votar(cenario.iano, cenario.veiculo, 0, 1)


def test_empate_abre_o_turno_seguinte_so_na_categoria_empatada() -> None:
    """Decisão 28: o sistema desfaz o empate sozinho, sem mostrar o placar."""
    cenario = CenarioDeVotacao()
    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)
    cenario.votar(cenario.bia, cenario.veiculo, 1, 0)  # empate geral: 3 a 3
    for eleitor in (cenario.iano, cenario.bia):
        cenario.votar(eleitor, cenario.crianca, 0, 1)
    cenario.confirmar(cenario.iano)

    resultado = cenario.confirmar(cenario.bia)

    assert resultado.turno_encerrado
    assert not resultado.votacao.encerrada
    assert resultado.votacao.turno_atual == 2
    desempate = cenario.turno_aberto(cenario.veiculo)
    assert desempate is not None
    assert desempate.numero == 2
    assert desempate.modo is ModoDeVotacao.CLASSIFICACAO
    assert desempate.candidatas == cenario.veiculo.candidatas
    assert cenario.turno_aberto(cenario.crianca) is None


def test_no_turno_seguinte_os_mesmos_eleitores_votam_numa_cedula_nova() -> None:
    """Interpretação 12: o 2º turno é da mesma votação, com os mesmos eleitores."""
    cenario = CenarioDeVotacao()
    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)
    cenario.votar(cenario.bia, cenario.veiculo, 1, 0)
    for eleitor in (cenario.iano, cenario.bia):
        cenario.votar(eleitor, cenario.crianca, 0, 1)
        cenario.confirmar(eleitor)
    desempate = cenario.turno_aberto(cenario.veiculo)
    assert desempate is not None

    for eleitor in (cenario.iano, cenario.bia):
        cedula = cenario.votar(eleitor, desempate, 1, 0)
        assert cedula.turno == 2
    cenario.confirmar(cenario.iano)
    resultado = cenario.confirmar(cenario.bia)

    assert resultado.votacao.encerrada
    assert desempate.pontuacao == (2, 4)
    assert desempate.lideres == (cenario.veiculo.candidatas[1],)
