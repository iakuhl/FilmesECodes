"""Testes do caso de uso RegistrarVoto."""

from uuid import uuid4

import pytest

from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    AcaoForaDaFaseError,
    CategoriaForaDoTurnoError,
    CedulaConfirmadaError,
    MembroForaDaVotacaoError,
    VotacaoEncerradaError,
    VotoInvalidoError,
)
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, MembroId
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar
from tests.application.use_cases.cenario_de_votacao import AGORA, CenarioDeVotacao


def test_eleitor_vota_na_cedula_do_turno_atual() -> None:
    cenario = CenarioDeVotacao()

    cedula = cenario.votar(cenario.iano, cenario.veiculo, 1, 0)

    assert cedula.turno == 1
    assert cedula.membro_id == cenario.iano
    assert not cedula.confirmada
    guardada = cenario.cedulas.buscar(cenario.votacao.id, 1, cenario.iano)
    assert guardada is not None
    assert guardada.escolhas == {
        cenario.veiculo.categoria_id: (cenario.veiculo.candidatas[1], cenario.veiculo.candidatas[0])
    }


def test_votos_em_varias_categorias_vao_para_a_mesma_cedula() -> None:
    cenario = CenarioDeVotacao()

    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)
    cedula = cenario.votar(cenario.iano, cenario.crianca, 0, 1)

    assert cedula.categorias_votadas == {
        cenario.veiculo.categoria_id,
        cenario.crianca.categoria_id,
    }
    assert len(cenario.cedulas.listar_por_turno(cenario.votacao.id, 1)) == 1


def test_voto_pode_ser_trocado_ate_a_confirmacao() -> None:
    cenario = CenarioDeVotacao()
    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)

    cedula = cenario.votar(cenario.iano, cenario.veiculo, 1, 0)

    assert cedula.escolhas[cenario.veiculo.categoria_id][0] == cenario.veiculo.candidatas[1]


def test_cedula_confirmada_nao_aceita_voto() -> None:
    cenario = CenarioDeVotacao()
    cenario.votar(cenario.iano, cenario.veiculo, 0, 1)
    cenario.votar(cenario.iano, cenario.crianca, 0, 1)
    cenario.confirmar(cenario.iano)

    with pytest.raises(CedulaConfirmadaError):
        cenario.votar(cenario.iano, cenario.veiculo, 1, 0)


def test_quem_nao_estava_ativo_no_inicio_nao_vota() -> None:
    """Decisão 23: os eleitores ficam definidos quando a votação começa."""
    cenario = CenarioDeVotacao()

    with pytest.raises(MembroForaDaVotacaoError):
        cenario.votar(MembroId(uuid4()), cenario.veiculo, 0, 1)


def test_voto_invalido_e_recusado() -> None:
    cenario = CenarioDeVotacao()

    with pytest.raises(VotoInvalidoError):
        cenario.votar(cenario.iano, cenario.veiculo, 0, 0)
    assert cenario.cedulas.buscar(cenario.votacao.id, 1, cenario.iano) is None


def test_edicao_fora_da_votacao_nao_aceita_votos() -> None:
    cenario = CenarioDeVotacao()
    cenario.temporada.avancar_para(StatusTemporadaOscar.APURADA)

    with pytest.raises(AcaoForaDaFaseError):
        cenario.votar(cenario.iano, cenario.veiculo, 0, 1)


def test_votacao_terminada_nao_aceita_votos() -> None:
    cenario = CenarioDeVotacao()
    cenario.votacao.encerrar(AGORA)

    with pytest.raises(VotacaoEncerradaError):
        cenario.votar(cenario.iano, cenario.veiculo, 0, 1)


def test_categoria_ja_decidida_nao_aceita_votos() -> None:
    cenario = CenarioDeVotacao()
    cenario.veiculo.apurar(
        [(cenario.veiculo.candidatas[0], cenario.veiculo.candidatas[1])], momento=AGORA
    )

    with pytest.raises(CategoriaForaDoTurnoError, match="Melhor veículo"):
        cenario.votar(cenario.iano, cenario.veiculo, 0, 1)


def test_categoria_inexistente() -> None:
    cenario = CenarioDeVotacao()

    with pytest.raises(EntidadeNaoEncontradaError):
        cenario.registrar_voto.executar(
            categoria_id=CategoriaOscarId(uuid4()), membro_id=cenario.iano, escolhas=[]
        )
