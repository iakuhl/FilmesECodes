"""Testes do caso de uso RegistrarSessaoExibicao."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.registrar_sessao_exibicao import (
    RegistrarSessaoExibicao,
)
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.exceptions.indicacao import TransicaoDeStatusInvalidaError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId, RodadaId
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.sessao_repositorio_fake import SessaoRepositorioFake


def _nova_indicacao() -> Indicacao:
    return Indicacao.criar(
        rodada_id=RodadaId(uuid4()),
        membro_id=MembroId(uuid4()),
        filme_id=FilmeId(uuid4()),
        data_indicacao=date(2024, 1, 1),
    )


def test_registrar_sessao_para_indicacao_sorteada() -> None:
    indicacoes = IndicacaoRepositorioFake()
    sessoes = SessaoRepositorioFake()
    indicacao = _nova_indicacao()
    indicacao.marcar_sorteada()
    indicacoes.salvar(indicacao)
    caso_de_uso = RegistrarSessaoExibicao(sessoes, indicacoes, RelogioFake(datetime(2024, 1, 7)))
    membros_presentes = frozenset({MembroId(uuid4())})

    sessao = caso_de_uso.executar(indicacao_id=indicacao.id, membros_presentes=membros_presentes)

    assert sessao.indicacao_id == indicacao.id
    assert indicacoes.buscar_por_id(indicacao.id).status is StatusIndicacao.ASSISTIDA  # type: ignore[union-attr]


def test_registrar_sessao_para_indicacao_ainda_pendente_levanta_erro() -> None:
    indicacoes = IndicacaoRepositorioFake()
    indicacao = _nova_indicacao()
    indicacoes.salvar(indicacao)
    caso_de_uso = RegistrarSessaoExibicao(
        SessaoRepositorioFake(), indicacoes, RelogioFake(datetime(2024, 1, 7))
    )

    with pytest.raises(TransicaoDeStatusInvalidaError):
        caso_de_uso.executar(indicacao_id=indicacao.id, membros_presentes=frozenset())
