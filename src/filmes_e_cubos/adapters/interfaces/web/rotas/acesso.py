"""Entrar e sair: a senha única do clube (decisão 35 de docs/PENDENCIAS.md)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, Request
from starlette.responses import Response

from filmes_e_cubos.adapters.interfaces.acesso import (
    CHAVE_DA_SESSAO,
    PAGINA_DE_ENTRADA,
    destino_seguro,
    senha_confere,
)
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina, redirecionar

roteador = APIRouter()


@roteador.get(PAGINA_DE_ENTRADA)
def entrar(request: Request, proximo: str = "/") -> Response:
    if request.session.get(CHAVE_DA_SESSAO) is True:
        return redirecionar(destino_seguro(proximo))
    return pagina(request, "entrar.html", proximo=destino_seguro(proximo), erro=None)


@roteador.post(PAGINA_DE_ENTRADA)
def conferir_senha(
    request: Request,
    senha: Annotated[str, Form()] = "",
    proximo: Annotated[str, Form()] = "/",
) -> Response:
    senha_do_clube = request.app.state.senha
    if senha_do_clube and senha_confere(senha, senha_do_clube):
        request.session[CHAVE_DA_SESSAO] = True
        return redirecionar(destino_seguro(proximo))
    return pagina(
        request,
        "entrar.html",
        status_code=401,
        proximo=destino_seguro(proximo),
        erro="Senha incorreta.",
    )


@roteador.post("/sair")
def sair(request: Request) -> Response:
    request.session.clear()
    return redirecionar(PAGINA_DE_ENTRADA)
