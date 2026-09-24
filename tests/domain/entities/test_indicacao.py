"""Testes da entidade Indicacao."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.exceptions.indicacao import TransicaoDeStatusInvalidaError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId, RodadaId
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao


def _criar_indicacao() -> Indicacao:
    return Indicacao.criar(
        rodada_id=RodadaId(uuid4()),
        membro_id=MembroId(uuid4()),
        filme_id=FilmeId(uuid4()),
        data_indicacao=date(2024, 1, 1),
    )


def test_indicacao_nasce_pendente() -> None:
    indicacao = _criar_indicacao()

    assert indicacao.status is StatusIndicacao.PENDENTE


def test_marcar_sorteada_a_partir_de_pendente() -> None:
    indicacao = _criar_indicacao()

    indicacao.marcar_sorteada()

    assert indicacao.status is StatusIndicacao.SORTEADA


def test_marcar_sorteada_quando_ja_sorteada_levanta_erro() -> None:
    indicacao = _criar_indicacao()
    indicacao.marcar_sorteada()

    with pytest.raises(TransicaoDeStatusInvalidaError):
        indicacao.marcar_sorteada()


def test_marcar_assistida_a_partir_de_sorteada() -> None:
    indicacao = _criar_indicacao()
    indicacao.marcar_sorteada()

    indicacao.marcar_assistida()

    assert indicacao.status is StatusIndicacao.ASSISTIDA


def test_marcar_assistida_sem_ter_sido_sorteada_levanta_erro() -> None:
    indicacao = _criar_indicacao()

    with pytest.raises(TransicaoDeStatusInvalidaError):
        indicacao.marcar_assistida()
