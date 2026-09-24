"""Testes de `CriterioEscolhaInformada`."""

from __future__ import annotations

from uuid import uuid4

import pytest

from filmes_e_cubos.adapters.servicos.criterio_apuracao_escolha_informada import (
    CriterioEscolhaInformada,
)
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.exceptions.oscar import NomeacaoInvalidaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    NomeacaoOscarId,
)


def _nomeacoes(quantidade: int) -> list[NomeacaoOscar]:
    categoria_id = CategoriaOscarId(uuid4())
    return [
        NomeacaoOscar.criar(
            categoria_id=categoria_id,
            filme_id=FilmeId(uuid4()),
            indicado_por_membro_id=MembroId(uuid4()),
        )
        for _ in range(quantidade)
    ]


def test_devolve_a_nomeacao_escolhida() -> None:
    nomeacoes = _nomeacoes(3)

    vencedora = CriterioEscolhaInformada(nomeacoes[1].id).escolher_vencedora(nomeacoes)

    assert vencedora is nomeacoes[1]


def test_escolha_que_nao_concorre_na_categoria_e_recusada() -> None:
    criterio = CriterioEscolhaInformada(NomeacaoOscarId(uuid4()))

    with pytest.raises(NomeacaoInvalidaError):
        criterio.escolher_vencedora(_nomeacoes(2))
