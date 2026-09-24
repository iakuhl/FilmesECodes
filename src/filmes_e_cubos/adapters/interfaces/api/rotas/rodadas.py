"""Rotas do ciclo de vida de uma rodada de indicações."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from filmes_e_cubos.adapters.interfaces.api.dependencias import ContextoDep
from filmes_e_cubos.adapters.interfaces.api.esquemas import RodadaSaida
from filmes_e_cubos.adapters.interfaces.consultas import (
    obter_clube,
    obter_rodada,
    obter_rodada_aberta,
)
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, RodadaId

roteador = APIRouter(tags=["rodadas"])


@roteador.get("/clubes/{clube_id}/rodadas", summary="Lista as rodadas de um clube")
def listar_rodadas(clube_id: UUID, contexto: ContextoDep) -> list[RodadaSaida]:
    clube = obter_clube(contexto.clubes, clube_id)
    rodadas = contexto.rodadas.listar_por_clube(clube.id)
    return [RodadaSaida.de_dominio(rodada) for rodada in rodadas]


@roteador.post(
    "/clubes/{clube_id}/rodadas",
    status_code=status.HTTP_201_CREATED,
    summary="Abre uma nova rodada",
    description="Falha com 409 se o clube já tiver uma rodada aberta.",
)
def abrir_rodada(clube_id: UUID, contexto: ContextoDep) -> RodadaSaida:
    rodada = contexto.abrir_nova_rodada.executar(clube_id=ClubeId(clube_id))
    return RodadaSaida.de_dominio(rodada)


@roteador.get(
    "/clubes/{clube_id}/rodadas/aberta",
    summary="Consulta a rodada aberta do clube",
    description="404 quando o clube não tem rodada aberta.",
)
def consultar_rodada_aberta(clube_id: UUID, contexto: ContextoDep) -> RodadaSaida:
    clube = obter_clube(contexto.clubes, clube_id)
    return RodadaSaida.de_dominio(obter_rodada_aberta(contexto.rodadas, clube))


@roteador.get("/rodadas/{rodada_id}", summary="Consulta uma rodada")
def consultar_rodada(rodada_id: UUID, contexto: ContextoDep) -> RodadaSaida:
    return RodadaSaida.de_dominio(obter_rodada(contexto.rodadas, rodada_id))


@roteador.post(
    "/rodadas/{rodada_id}/encerrar",
    summary="Encerra a rodada",
    description="Falha com 409 se alguma indicação da rodada ainda não tiver sido assistida.",
)
def encerrar_rodada(rodada_id: UUID, contexto: ContextoDep) -> RodadaSaida:
    rodada = contexto.encerrar_rodada.executar(rodada_id=RodadaId(rodada_id))
    return RodadaSaida.de_dominio(rodada)
