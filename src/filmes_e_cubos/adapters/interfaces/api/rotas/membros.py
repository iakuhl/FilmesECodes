"""Rotas de membros de um clube."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from filmes_e_cubos.adapters.interfaces.api.esquemas import MembroSaida, NovoMembro
from filmes_e_cubos.adapters.interfaces.consultas import obter_clube, obter_membro
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, MembroId

roteador = APIRouter(tags=["membros"])


@roteador.get("/clubes/{clube_id}/membros", summary="Lista os membros de um clube")
def listar_membros(
    clube_id: UUID, contexto: ContextoDep, apenas_ativos: bool = False
) -> list[MembroSaida]:
    clube = obter_clube(contexto.clubes, clube_id)
    membros = (
        contexto.membros.listar_ativos_por_clube(clube.id)
        if apenas_ativos
        else contexto.membros.listar_por_clube(clube.id)
    )
    return [MembroSaida.de_dominio(membro) for membro in membros]


@roteador.post(
    "/clubes/{clube_id}/membros",
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um membro, já ativo",
)
def cadastrar_membro(clube_id: UUID, novo: NovoMembro, contexto: ContextoDep) -> MembroSaida:
    membro = contexto.cadastrar_membro.executar(
        clube_id=ClubeId(clube_id), nome=novo.nome, apelido=novo.apelido
    )
    return MembroSaida.de_dominio(membro)


@roteador.get("/membros/{membro_id}", summary="Consulta um membro")
def consultar_membro(membro_id: UUID, contexto: ContextoDep) -> MembroSaida:
    return MembroSaida.de_dominio(obter_membro(contexto.membros, membro_id))


@roteador.post(
    "/membros/{membro_id}/desativar",
    summary="Desativa um membro",
    description="O histórico do membro (indicações, avaliações, troféus) permanece intacto; "
    "ele só deixa de contar para as próximas rodadas.",
)
def desativar_membro(membro_id: UUID, contexto: ContextoDep) -> MembroSaida:
    contexto.desativar_membro.executar(membro_id=MembroId(membro_id))
    return MembroSaida.de_dominio(obter_membro(contexto.membros, membro_id))


@roteador.post(
    "/membros/{membro_id}/reativar",
    summary="Reativa um membro",
    description="O membro volta a indicar, avaliar e votar, com o histórico que já tinha.",
)
def reativar_membro(membro_id: UUID, contexto: ContextoDep) -> MembroSaida:
    contexto.reativar_membro.executar(membro_id=MembroId(membro_id))
    return MembroSaida.de_dominio(obter_membro(contexto.membros, membro_id))
