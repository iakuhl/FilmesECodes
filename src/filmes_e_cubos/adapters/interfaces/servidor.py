"""Servidor HTTP do Filmes e Cubos: monta o app ASGI e o entry point que o serve.

`criar_aplicacao` junta, num único app, tudo o que é servido por HTTP —
hoje, a API JSON, montada em `/api/v1` como um sub-app com seu próprio
contrato de erros e sua própria documentação (`/api/v1/docs`). O
middleware `EscritasEmFila` envolve o conjunto inteiro.

O entry point `filmes-e-cubos-servidor` roda esse app com o uvicorn. O
padrão é ouvir só em `127.0.0.1`: ainda não há autenticação, então expor
o servidor na rede é uma decisão explícita de quem o roda (`--host`).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Final

import typer
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from filmes_e_cubos.adapters.composicao import (
    CAMINHO_BANCO_PADRAO,
    VARIAVEL_DE_AMBIENTE_BANCO,
    Contexto,
)
from filmes_e_cubos.adapters.interfaces.api.app import criar_api
from filmes_e_cubos.adapters.interfaces.escritas_em_fila import EscritasEmFila
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine

PREFIXO_DA_API: Final = "/api/v1"


def criar_aplicacao(contexto: Contexto) -> FastAPI:
    """O app ASGI completo, sobre um `Contexto` já montado."""
    aplicacao = FastAPI(
        title="Filmes e Cubos",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    aplicacao.mount(PREFIXO_DA_API, criar_api(contexto))
    aplicacao.add_middleware(EscritasEmFila)

    @aplicacao.get("/", include_in_schema=False)
    def raiz() -> RedirectResponse:
        return RedirectResponse(f"{PREFIXO_DA_API}/docs")

    return aplicacao


def criar_aplicacao_do_ambiente() -> FastAPI:
    """Fábrica chamada pelo uvicorn: lê o caminho do banco do ambiente.

    O uvicorn recebe a fábrica como texto (`modulo:funcao`) — é o que
    permite recarregar o código em desenvolvimento —, então a
    configuração chega por variável de ambiente, e não por argumento.
    """
    caminho = Path(os.environ.get(VARIAVEL_DE_AMBIENTE_BANCO, str(CAMINHO_BANCO_PADRAO)))
    return criar_aplicacao(Contexto(criar_engine(caminho)))


comando = typer.Typer(add_completion=False)


@comando.command()
def servir(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            help="Endereço em que o servidor escuta. O padrão só aceita conexões desta "
            "máquina; use 0.0.0.0 para expor na rede (não há autenticação ainda).",
        ),
    ] = "127.0.0.1",
    porta: Annotated[int, typer.Option("--porta", help="Porta TCP do servidor.")] = 8000,
    db_path: Annotated[
        Path,
        typer.Option(
            "--db-path",
            envvar=VARIAVEL_DE_AMBIENTE_BANCO,
            help="Arquivo SQLite onde os dados do clube são guardados.",
        ),
    ] = CAMINHO_BANCO_PADRAO,
    recarregar: Annotated[
        bool,
        typer.Option(
            "--recarregar", help="Reinicia ao detectar mudanças no código (desenvolvimento)."
        ),
    ] = False,
) -> None:
    """Serve a API do Filmes e Cubos (documentação em /api/v1/docs)."""
    os.environ[VARIAVEL_DE_AMBIENTE_BANCO] = str(db_path)
    uvicorn.run(
        f"{__name__}:criar_aplicacao_do_ambiente",
        factory=True,
        host=host,
        port=porta,
        reload=recarregar,
    )
