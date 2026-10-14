"""Sessões: registrar quem estava presente e avaliar o filme."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request
from starlette.responses import Response

from filmes_e_cubos.adapters.interfaces.consultas import obter_clube
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.adapters.interfaces.web.escopo import (
    indicacao_do_clube,
    membro_do_clube,
    sessao_do_clube,
)
from filmes_e_cubos.adapters.interfaces.web.formatacao import notas_da_escala
from filmes_e_cubos.adapters.interfaces.web.formularios import (
    VALOR_DORMINHOCO,
    id_escolhido,
    nota_ou_dorminhoco,
    texto_opcional,
)
from filmes_e_cubos.adapters.interfaces.web.mensagens import avisar, recusas_viram_avisos
from filmes_e_cubos.adapters.interfaces.web.painel import sessao_na_pagina
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina, redirecionar
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, MembroId

roteador = APIRouter(prefix="/clubes/{clube_id}")


@roteador.get("/indicacoes/{indicacao_id}/sessao")
def nova_sessao(
    request: Request, clube_id: UUID, indicacao_id: UUID, contexto: ContextoDep
) -> Response:
    """Quem estava presente: os membros ativos vêm marcados (a presença padrão)."""
    clube = obter_clube(contexto.clubes, clube_id)
    indicacao = indicacao_do_clube(contexto, clube, indicacao_id)
    sessao = contexto.sessoes.buscar_por_indicacao(indicacao.id)
    if sessao is not None:
        return redirecionar(f"/clubes/{clube.id}/sessoes/{sessao.id}")
    return pagina(
        request,
        "nova_sessao.html",
        clube=clube,
        secao="painel",
        indicacao=indicacao,
        filme=contexto.filmes.buscar_por_id(indicacao.filme_id),
        membros=contexto.membros.listar_ativos_por_clube(clube.id),
    )


@roteador.post("/indicacoes/{indicacao_id}/sessao")
def registrar_sessao(
    request: Request,
    clube_id: UUID,
    indicacao_id: UUID,
    contexto: ContextoDep,
    presentes: Annotated[list[str] | None, Form()] = None,
) -> Response:
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        indicacao = indicacao_do_clube(contexto, clube, indicacao_id)
        membros = frozenset(
            membro_do_clube(contexto, clube, id_escolhido(presente, campo="quem estava")).id
            for presente in presentes or []
        )
        sessao = contexto.registrar_sessao_exibicao.executar(
            indicacao_id=IndicacaoId(indicacao.id), membros_presentes=membros
        )
        avisar(request, "sucesso", "Sessão registrada. Agora é avaliar!")
        return redirecionar(f"/clubes/{clube_id}/sessoes/{sessao.id}")
    return redirecionar(f"/clubes/{clube_id}/indicacoes/{indicacao_id}/sessao")


@roteador.get("/sessoes/{sessao_id}")
def sessao(request: Request, clube_id: UUID, sessao_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    escolhida = sessao_do_clube(contexto, clube, sessao_id)
    return pagina(
        request,
        "sessao.html",
        clube=clube,
        secao="painel",
        sessao=sessao_na_pagina(contexto, escolhida),
        notas=notas_da_escala(clube.configuracao.escala_avaliacao),
        dorminhoco=VALOR_DORMINHOCO,
    )


@roteador.post("/sessoes/{sessao_id}/avaliacoes")
def avaliar(
    request: Request,
    clube_id: UUID,
    sessao_id: UUID,
    contexto: ContextoDep,
    membro_id: Annotated[str, Form()] = "",
    nota: Annotated[str, Form()] = "",
    comentario: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        escolhida = sessao_do_clube(contexto, clube, sessao_id)
        membro = membro_do_clube(contexto, clube, id_escolhido(membro_id, campo="quem avalia"))
        contexto.avaliar_filme.executar(
            sessao_id=escolhida.id,
            membro_id=MembroId(membro.id),
            nota=nota_ou_dorminhoco(nota),
            comentario=texto_opcional(comentario),
        )
        avisar(request, "sucesso", f"Avaliação de {membro.nome} registrada.")
    return redirecionar(f"/clubes/{clube_id}/sessoes/{sessao_id}")
