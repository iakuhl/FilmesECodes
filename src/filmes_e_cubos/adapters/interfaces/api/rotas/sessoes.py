"""Rotas das sessões em que o clube assistiu a um filme."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, status

from filmes_e_cubos.adapters.interfaces.api.dependencias import ContextoDep
from filmes_e_cubos.adapters.interfaces.api.esquemas import NovaSessao, SessaoSaida
from filmes_e_cubos.adapters.interfaces.consultas import obter_indicacao, obter_sessao
from filmes_e_cubos.adapters.interfaces.convencoes import presenca_padrao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId

roteador = APIRouter(tags=["sessões"])


@roteador.post(
    "/indicacoes/{indicacao_id}/sessao",
    status_code=status.HTTP_201_CREATED,
    summary="Registra a sessão de uma indicação",
    description="Marca a indicação como assistida. O corpo é opcional: sem `membros_presentes`, "
    "assume todos os membros ativos do clube.",
)
def registrar_sessao(
    indicacao_id: UUID,
    contexto: ContextoDep,
    nova: Annotated[NovaSessao | None, Body()] = None,
) -> SessaoSaida:
    indicacao = obter_indicacao(contexto.indicacoes, indicacao_id)
    presentes = nova.membros_presentes if nova is not None else None
    membros_presentes = (
        frozenset(MembroId(membro_id) for membro_id in presentes)
        if presentes is not None
        else presenca_padrao(indicacao, contexto.rodadas, contexto.membros)
    )
    sessao = contexto.registrar_sessao_exibicao.executar(
        indicacao_id=indicacao.id, membros_presentes=membros_presentes
    )
    return SessaoSaida.de_dominio(sessao)


@roteador.get(
    "/indicacoes/{indicacao_id}/sessao",
    summary="Consulta a sessão de uma indicação",
    description="404 enquanto a indicação não tiver sido assistida.",
)
def consultar_sessao_da_indicacao(indicacao_id: UUID, contexto: ContextoDep) -> SessaoSaida:
    indicacao = obter_indicacao(contexto.indicacoes, indicacao_id)
    sessao = contexto.sessoes.buscar_por_indicacao(indicacao.id)
    if sessao is None:
        raise EntidadeNaoEncontradaError(f"A indicação {indicacao_id} ainda não tem sessão.")
    return SessaoSaida.de_dominio(sessao)


@roteador.get("/sessoes/{sessao_id}", summary="Consulta uma sessão")
def consultar_sessao(sessao_id: UUID, contexto: ContextoDep) -> SessaoSaida:
    return SessaoSaida.de_dominio(obter_sessao(contexto.sessoes, sessao_id))
