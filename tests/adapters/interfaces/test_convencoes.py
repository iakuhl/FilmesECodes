"""Testes das convenções compartilhadas pelas interfaces.

Usam os repositórios in-memory da camada de aplicação: as convenções só
leem de ports, então não há nada de infraestrutura a exercitar aqui — a
costura com o banco real é coberta pelos testes de cada interface.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.adapters.interfaces.convencoes import (
    clube_da_sessao,
    nome_padrao_da_temporada,
    presenca_padrao,
)
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    ClubeId,
    FilmeId,
    IndicacaoId,
    MembroId,
    RodadaId,
)
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake

HOJE = date(2025, 3, 1)


def _rodada(rodadas: RodadaRepositorioFake, clube_id: ClubeId) -> Rodada:
    rodada = Rodada.abrir(clube_id=clube_id, numero=1, data_inicio=HOJE)
    rodadas.salvar(rodada)
    return rodada


def _indicacao(rodada_id: RodadaId) -> Indicacao:
    return Indicacao.criar(
        rodada_id=rodada_id,
        membro_id=MembroId(uuid4()),
        filme_id=FilmeId(uuid4()),
        data_indicacao=HOJE,
    )


def test_nome_padrao_da_temporada_combina_clube_e_ano() -> None:
    assert nome_padrao_da_temporada("Filmes e Cubos", 2025) == "Óscar do Filmes e Cubos 2025"


def test_presenca_padrao_sao_os_membros_ativos_do_clube_da_rodada() -> None:
    clube_id = ClubeId(uuid4())
    rodadas = RodadaRepositorioFake()
    membros = MembroRepositorioFake()
    ativo = Membro.criar(clube_id=clube_id, nome="Iano", data_ingresso=HOJE)
    inativo = Membro.criar(clube_id=clube_id, nome="Bia", data_ingresso=HOJE)
    inativo.desativar()
    de_outro_clube = Membro.criar(clube_id=ClubeId(uuid4()), nome="Duda", data_ingresso=HOJE)
    for membro in (ativo, inativo, de_outro_clube):
        membros.salvar(membro)
    indicacao = _indicacao(_rodada(rodadas, clube_id).id)

    assert presenca_padrao(indicacao, rodadas, membros) == frozenset({ativo.id})


def test_presenca_padrao_sem_rodada_falha() -> None:
    indicacao = _indicacao(RodadaId(uuid4()))

    with pytest.raises(EntidadeNaoEncontradaError):
        presenca_padrao(indicacao, RodadaRepositorioFake(), MembroRepositorioFake())


def test_clube_da_sessao_segue_indicacao_e_rodada() -> None:
    clube_id = ClubeId(uuid4())
    rodadas = RodadaRepositorioFake()
    indicacoes = IndicacaoRepositorioFake()
    indicacao = _indicacao(_rodada(rodadas, clube_id).id)
    indicacoes.salvar(indicacao)
    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao.id, data_sessao=HOJE, membros_presentes=frozenset()
    )

    assert clube_da_sessao(sessao, indicacoes, rodadas) == clube_id


def test_clube_da_sessao_sem_indicacao_falha() -> None:
    sessao = SessaoExibicao.registrar(
        indicacao_id=IndicacaoId(uuid4()), data_sessao=HOJE, membros_presentes=frozenset()
    )

    with pytest.raises(EntidadeNaoEncontradaError):
        clube_da_sessao(sessao, IndicacaoRepositorioFake(), RodadaRepositorioFake())
