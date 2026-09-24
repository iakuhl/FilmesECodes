"""Rotas de clubes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from filmes_e_cubos.adapters.interfaces.api.dependencias import ContextoDep
from filmes_e_cubos.adapters.interfaces.api.esquemas import ClubeSaida, NovoClube
from filmes_e_cubos.adapters.interfaces.consultas import obter_clube

roteador = APIRouter(tags=["clubes"])


@roteador.get("/clubes", summary="Lista os clubes")
def listar_clubes(contexto: ContextoDep) -> list[ClubeSaida]:
    return [ClubeSaida.de_dominio(clube) for clube in contexto.clubes.listar_todos()]


@roteador.post("/clubes", status_code=status.HTTP_201_CREATED, summary="Cria um clube")
def criar_clube(novo: NovoClube, contexto: ContextoDep) -> ClubeSaida:
    clube = contexto.criar_clube.executar(
        nome=novo.nome, configuracao=novo.configuracao_de_dominio()
    )
    return ClubeSaida.de_dominio(clube)


@roteador.get("/clubes/{clube_id}", summary="Consulta um clube")
def consultar_clube(clube_id: UUID, contexto: ContextoDep) -> ClubeSaida:
    return ClubeSaida.de_dominio(obter_clube(contexto.clubes, clube_id))
