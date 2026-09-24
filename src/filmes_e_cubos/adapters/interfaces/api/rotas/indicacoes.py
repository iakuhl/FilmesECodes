"""Rotas de indicação de filmes e de sorteio da próxima sessão."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from filmes_e_cubos.adapters.interfaces.api.dependencias import ContextoDep
from filmes_e_cubos.adapters.interfaces.api.esquemas import (
    IndicacaoSaida,
    NovaIndicacao,
    NovaIndicacaoDemocracia,
    SorteioSaida,
)
from filmes_e_cubos.adapters.interfaces.consultas import (
    obter_clube,
    obter_indicacao,
    obter_rodada,
)
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId, RodadaId

roteador = APIRouter(tags=["indicações e sorteios"])


@roteador.get("/rodadas/{rodada_id}/indicacoes", summary="Lista as indicações de uma rodada")
def listar_indicacoes(rodada_id: UUID, contexto: ContextoDep) -> list[IndicacaoSaida]:
    rodada = obter_rodada(contexto.rodadas, rodada_id)
    return [
        IndicacaoSaida.de_dominio(indicacao)
        for indicacao in contexto.indicacoes.listar_por_rodada(rodada.id)
    ]


@roteador.post(
    "/rodadas/{rodada_id}/indicacoes",
    status_code=status.HTTP_201_CREATED,
    summary="Registra a indicação semanal de um membro",
    description="Um membro indica uma vez por rodada, e a rodada respeita o tamanho "
    "configurado no clube.",
)
def indicar_filme(rodada_id: UUID, nova: NovaIndicacao, contexto: ContextoDep) -> IndicacaoSaida:
    indicacao = contexto.indicar_filme.executar(
        rodada_id=RodadaId(rodada_id),
        membro_id=MembroId(nova.membro_id),
        filme_id=FilmeId(nova.filme_id),
    )
    return IndicacaoSaida.de_dominio(indicacao)


@roteador.post(
    "/clubes/{clube_id}/indicacoes-democracia",
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona uma sessão democracia à rodada aberta",
    description="Sessão extra escolhida em grupo, para quando a sessão programada é adiada. "
    "Não tem membro indicador e não consome a cota da rodada.",
)
def adicionar_democracia(
    clube_id: UUID, nova: NovaIndicacaoDemocracia, contexto: ContextoDep
) -> IndicacaoSaida:
    clube = obter_clube(contexto.clubes, clube_id)
    indicacao = contexto.adicionar_filme_democracia.executar(
        clube_id=clube.id, filme_id=FilmeId(nova.filme_id)
    )
    return IndicacaoSaida.de_dominio(indicacao)


@roteador.get("/indicacoes/{indicacao_id}", summary="Consulta uma indicação")
def consultar_indicacao(indicacao_id: UUID, contexto: ContextoDep) -> IndicacaoSaida:
    return IndicacaoSaida.de_dominio(obter_indicacao(contexto.indicacoes, indicacao_id))


@roteador.get("/rodadas/{rodada_id}/sorteios", summary="Lista os sorteios de uma rodada")
def listar_sorteios(rodada_id: UUID, contexto: ContextoDep) -> list[SorteioSaida]:
    rodada = obter_rodada(contexto.rodadas, rodada_id)
    sorteios = contexto.sorteios.listar_por_rodada(rodada.id)
    return [SorteioSaida.de_dominio(sorteio) for sorteio in sorteios]


@roteador.post(
    "/rodadas/{rodada_id}/sorteios",
    status_code=status.HTTP_201_CREATED,
    summary="Sorteia uma das indicações pendentes",
    description="Apoio opcional: nada impede de registrar a sessão de uma indicação que "
    "nunca passou pelo sorteio.",
)
def sortear(rodada_id: UUID, contexto: ContextoDep) -> SorteioSaida:
    sorteio = contexto.realizar_sorteio.executar(rodada_id=RodadaId(rodada_id))
    return SorteioSaida.de_dominio(sorteio)
