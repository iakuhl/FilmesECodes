"""A interface web: páginas renderizadas no servidor (decisão 1 de docs/PENDENCIAS.md).

`criar_web` monta o app FastAPI das páginas, que é também o app raiz do
servidor: a API entra nele, montada em `/api/v1` (ver `servidor.py`).

Toda ação segue o padrão Post/Redirect/Get: o formulário faz um POST, a
rota roda o caso de uso dentro de `recusas_viram_avisos`, registra o
aviso de sucesso e redireciona com 303 para uma página comum — que exibe
o aviso, de sucesso ou de recusa.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.web.erros import registrar_paginas_de_erro
from filmes_e_cubos.adapters.interfaces.web.rotas import acesso, inicio

DIRETORIO_DOS_ESTATICOS: Final = Path(__file__).parent / "estaticos"


def criar_web(contexto: Contexto, *, senha: str | None = None) -> FastAPI:
    """O app das páginas, sobre um `Contexto` já montado.

    `senha` é a senha do clube que a página de entrada confere; a
    proteção das demais páginas é do middleware `ProtecaoPorSenha`.
    """
    web = FastAPI(title="Filmes e Cubos", docs_url=None, redoc_url=None, openapi_url=None)
    web.state.contexto = contexto
    web.state.senha = senha
    web.mount("/estaticos", StaticFiles(directory=DIRETORIO_DOS_ESTATICOS), name="estaticos")

    @web.get("/favicon.ico", include_in_schema=False)
    def icone() -> RedirectResponse:
        return RedirectResponse("/estaticos/icone.svg")

    for modulo in (acesso, inicio):
        web.include_router(modulo.roteador)
    registrar_paginas_de_erro(web)
    return web
