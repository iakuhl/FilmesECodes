"""Início: escolher (ou criar) o clube e o painel dele."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request
from starlette.responses import Response

from filmes_e_cubos.adapters.interfaces.consultas import obter_clube
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.adapters.interfaces.web.formularios import inteiro_opcional
from filmes_e_cubos.adapters.interfaces.web.mensagens import avisar, recusas_viram_avisos
from filmes_e_cubos.adapters.interfaces.web.painel import montar_painel
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina, redirecionar
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube

roteador = APIRouter()


@roteador.get("/")
def inicio(request: Request, contexto: ContextoDep) -> Response:
    """Sem clube, oferece criar; com um só, vai direto a ele; com vários, lista."""
    clubes = contexto.clubes.listar_todos()
    if len(clubes) == 1:
        return redirecionar(f"/clubes/{clubes[0].id}")
    return pagina(request, "inicio.html", clubes=clubes)


@roteador.post("/clubes")
def criar_clube(
    request: Request,
    contexto: ContextoDep,
    nome: Annotated[str, Form()] = "",
    tamanho_rodada: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        tamanho = inteiro_opcional(tamanho_rodada, campo="Indicações por rodada")
        padrao = ConfiguracaoClube.padrao()
        clube = contexto.criar_clube.executar(
            nome=nome,
            configuracao=ConfiguracaoClube(
                tamanho_rodada=tamanho if tamanho is not None else padrao.tamanho_rodada,
                escala_avaliacao=padrao.escala_avaliacao,
            ),
        )
        avisar(request, "sucesso", f"Clube {clube.nome} criado.")
        return redirecionar(f"/clubes/{clube.id}")
    return redirecionar("/")


@roteador.get("/clubes/{clube_id}")
def painel(request: Request, clube_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    return pagina(
        request, "painel.html", clube=clube, secao="painel", painel=montar_painel(contexto, clube)
    )
