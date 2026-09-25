"""Testes da entidade Cedula: votos alteráveis até a confirmação."""

from datetime import datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.exceptions.oscar import CedulaConfirmadaError, CedulaIncompletaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
    VotacaoOscarId,
)

MOMENTO = datetime(2024, 12, 20, 21, 0)
VEICULO, CRIANCA = CategoriaOscarId(uuid4()), CategoriaOscarId(uuid4())
A, B, C = (NomeacaoOscarId(uuid4()) for _ in range(3))


def _cedula() -> Cedula:
    return Cedula.criar(votacao_id=VotacaoOscarId(uuid4()), turno=1, membro_id=MembroId(uuid4()))


def test_cedula_nova_nao_tem_votos_nem_confirmacao() -> None:
    cedula = _cedula()

    assert cedula.escolhas == {}
    assert cedula.categorias_votadas == frozenset()
    assert not cedula.confirmada


def test_voto_pode_ser_trocado_antes_da_confirmacao() -> None:
    cedula = _cedula()

    cedula.votar(VEICULO, [A, B])
    cedula.votar(VEICULO, [C, A])

    assert cedula.escolhas == {VEICULO: (C, A)}


def test_confirmar_exige_voto_em_todas_as_categorias_do_turno() -> None:
    cedula = _cedula()
    cedula.votar(VEICULO, [A, B])

    with pytest.raises(CedulaIncompletaError):
        cedula.confirmar([VEICULO, CRIANCA], momento=MOMENTO)
    assert not cedula.confirmada


def test_cedula_confirmada_nao_muda_mais() -> None:
    """Decisão 25: confirmada, a cédula trava."""
    cedula = _cedula()
    cedula.votar(VEICULO, [A, B])
    cedula.confirmar([VEICULO], momento=MOMENTO)

    assert cedula.confirmada_em == MOMENTO
    with pytest.raises(CedulaConfirmadaError):
        cedula.votar(VEICULO, [B, A])
    with pytest.raises(CedulaConfirmadaError):
        cedula.confirmar([VEICULO], momento=MOMENTO)
    assert cedula.escolhas == {VEICULO: (A, B)}


def test_escolhas_devolve_uma_copia() -> None:
    cedula = _cedula()
    cedula.votar(VEICULO, [A, B])

    cedula.escolhas[VEICULO] = (C, A)

    assert cedula.escolhas == {VEICULO: (A, B)}
