"""Membros do clube: cadastrar, desativar e reativar."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request
from starlette.responses import Response

from filmes_e_cubos.adapters.interfaces.consultas import obter_clube
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.adapters.interfaces.web.escopo import membro_do_clube
from filmes_e_cubos.adapters.interfaces.web.formularios import texto_opcional
from filmes_e_cubos.adapters.interfaces.web.mensagens import avisar, recusas_viram_avisos
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina, redirecionar

roteador = APIRouter(prefix="/clubes/{clube_id}/membros")


@roteador.get("")
def membros(request: Request, clube_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    todos = contexto.membros.listar_por_clube(clube.id)
    # Ativos primeiro; dentro de cada grupo, a ordem alfabética do repositório.
    todos.sort(key=lambda membro: not membro.ativo)
    return pagina(request, "membros.html", clube=clube, secao="membros", membros=todos)


@roteador.post("")
def cadastrar(
    request: Request,
    clube_id: UUID,
    contexto: ContextoDep,
    nome: Annotated[str, Form()] = "",
    apelido: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        membro = contexto.cadastrar_membro.executar(
            clube_id=clube.id, nome=nome.strip(), apelido=texto_opcional(apelido)
        )
        avisar(request, "sucesso", f"{membro.nome} entrou no clube.")
    return redirecionar(f"/clubes/{clube_id}/membros")


@roteador.post("/{membro_id}/desativar")
def desativar(request: Request, clube_id: UUID, membro_id: UUID, contexto: ContextoDep) -> Response:
    with recusas_viram_avisos(request):
        membro = membro_do_clube(contexto, obter_clube(contexto.clubes, clube_id), membro_id)
        contexto.desativar_membro.executar(membro_id=membro.id)
        avisar(request, "sucesso", f"{membro.nome} foi desativado.")
    return redirecionar(f"/clubes/{clube_id}/membros")


@roteador.post("/{membro_id}/reativar")
def reativar(request: Request, clube_id: UUID, membro_id: UUID, contexto: ContextoDep) -> Response:
    """Só aparece para inativos (decisão 33); repetida, não é erro."""
    with recusas_viram_avisos(request):
        membro = membro_do_clube(contexto, obter_clube(contexto.clubes, clube_id), membro_id)
        contexto.reativar_membro.executar(membro_id=membro.id)
        avisar(request, "sucesso", f"{membro.nome} voltou a ser ativo.")
    return redirecionar(f"/clubes/{clube_id}/membros")
