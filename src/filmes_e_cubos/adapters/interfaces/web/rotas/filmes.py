"""Catálogo de filmes: cadastrar e corrigir a duração.

O catálogo é um só para todos os clubes; a página fica dentro do clube
só para manter a navegação.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request
from starlette.responses import Response

from filmes_e_cubos.adapters.interfaces.consultas import obter_clube, obter_filme
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.adapters.interfaces.web.formularios import inteiro_opcional, texto_opcional
from filmes_e_cubos.adapters.interfaces.web.mensagens import (
    FormularioInvalidoError,
    avisar,
    recusas_viram_avisos,
)
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina, redirecionar
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId

roteador = APIRouter(prefix="/clubes/{clube_id}/filmes")


@roteador.get("")
def filmes(request: Request, clube_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    return pagina(
        request, "filmes.html", clube=clube, secao="filmes", filmes=contexto.filmes.listar_todos()
    )


@roteador.post("")
def cadastrar(
    request: Request,
    clube_id: UUID,
    contexto: ContextoDep,
    titulo: Annotated[str, Form()] = "",
    ano_lancamento: Annotated[str, Form()] = "",
    diretor: Annotated[str, Form()] = "",
    duracao_minutos: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        filme = contexto.cadastrar_filme.executar(
            titulo=titulo.strip(),
            ano_lancamento=inteiro_opcional(ano_lancamento, campo="Ano"),
            diretor=texto_opcional(diretor),
            duracao_minutos=inteiro_opcional(duracao_minutos, campo="Duração"),
        )
        avisar(request, "sucesso", f"{filme.titulo} entrou no catálogo.")
    return redirecionar(f"/clubes/{clube_id}/filmes")


@roteador.post("/{filme_id}/duracao")
def definir_duracao(
    request: Request,
    clube_id: UUID,
    filme_id: UUID,
    contexto: ContextoDep,
    duracao_minutos: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        filme = obter_filme(contexto.filmes, filme_id)
        duracao = inteiro_opcional(duracao_minutos, campo="Duração")
        if duracao is None:
            raise FormularioInvalidoError("Informe a duração, em minutos.")
        contexto.definir_duracao_filme.executar(filme_id=FilmeId(filme.id), duracao_minutos=duracao)
        avisar(request, "sucesso", f"Duração de {filme.titulo} atualizada.")
    return redirecionar(f"/clubes/{clube_id}/filmes")
