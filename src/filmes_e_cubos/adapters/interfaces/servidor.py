"""Servidor HTTP do Filmes e Cubos: monta o app ASGI e o entry point que o serve.

`criar_aplicacao` junta, num único app, tudo o que é servido por HTTP: a
web na raiz e a API JSON montada em `/api/v1`, como um sub-app com o seu
próprio contrato de erros e a sua documentação (`/api/v1/docs`). Em volta
do conjunto, de fora para dentro: `EscritasEmFila`, a sessão (um cookie
assinado) e a proteção por senha do clube.

O entry point `filmes-e-cubos-servidor` roda esse app com o uvicorn; na
Vercel, quem o serve é o `app.py` da raiz. Sem senha configurada, o padrão
é ouvir só em `127.0.0.1`: expor o servidor na rede é uma decisão
explícita de quem o roda (`--host`).
"""

from __future__ import annotations

import os
import secrets
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Final

import typer
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from filmes_e_cubos.adapters.composicao import (
    CAMINHO_BANCO_PADRAO,
    VARIAVEL_DE_AMBIENTE_BANCO,
    VARIAVEL_DE_AMBIENTE_URL_DO_BANCO,
    Contexto,
)
from filmes_e_cubos.adapters.interfaces.acesso import (
    VARIAVEL_DE_AMBIENTE_CHAVE_SECRETA,
    VARIAVEL_DE_AMBIENTE_SENHA,
    ProtecaoPorSenha,
    chave_secreta_da_senha,
)
from filmes_e_cubos.adapters.interfaces.api.app import criar_api
from filmes_e_cubos.adapters.interfaces.escritas_em_fila import EscritasEmFila
from filmes_e_cubos.adapters.interfaces.web.app import criar_web
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import (
    criar_engine,
    criar_engine_da_url,
)

PREFIXO_DA_API: Final = "/api/v1"

VARIAVEL_DE_AMBIENTE_DA_VERCEL: Final = "VERCEL"
"""Definida pela própria Vercel nas funções que ela roda."""

_VALIDADE_DA_SESSAO: Final = timedelta(days=30)


def criar_aplicacao(
    contexto: Contexto,
    *,
    senha: str | None = None,
    exigir_senha: bool = False,
    chave_secreta: str | None = None,
    cookies_seguros: bool = False,
) -> FastAPI:
    """O app ASGI completo, sobre um `Contexto` já montado.

    `senha` protege o site e a API (decisão 35 de docs/PENDENCIAS.md);
    sem ela, nada é protegido — a menos que `exigir_senha`, quando o site
    sai do ar dizendo o que configurar. `chave_secreta` assina o cookie da
    sessão: sem ela, vem da senha (igual em todas as instâncias da
    Vercel) ou, sem senha, é sorteada a cada processo. `cookies_seguros`
    restringe o cookie a HTTPS.
    """
    if chave_secreta is None:
        chave_secreta = chave_secreta_da_senha(senha) if senha else secrets.token_urlsafe(32)
    aplicacao = criar_web(contexto, senha=senha)
    aplicacao.mount(PREFIXO_DA_API, criar_api(contexto))
    # `add_middleware` põe cada um por fora do anterior: a proteção roda
    # dentro da sessão, que lhe entrega o cookie já lido.
    aplicacao.add_middleware(ProtecaoPorSenha, senha=senha, exigir_senha=exigir_senha)
    aplicacao.add_middleware(
        SessionMiddleware,
        secret_key=chave_secreta,
        session_cookie="filmes_e_cubos",
        max_age=int(_VALIDADE_DA_SESSAO.total_seconds()),
        same_site="lax",
        https_only=cookies_seguros,
    )
    aplicacao.add_middleware(EscritasEmFila)
    return aplicacao


def criar_aplicacao_do_ambiente() -> FastAPI:
    """O app inteiro configurado pelo ambiente — o que o uvicorn e a Vercel servem.

    O uvicorn recebe a fábrica como texto (`modulo:funcao`) — é o que
    permite recarregar o código em desenvolvimento —, e a Vercel importa o
    `app` de `app.py`, na raiz do repositório. Nos dois casos, a
    configuração chega por variável de ambiente: `DATABASE_URL` (o
    Postgres da produção) ou, sem ela, `FILMES_E_CUBOS_DB` (o arquivo
    SQLite local); `FILMES_E_CUBOS_SENHA`, a senha do clube — que, na
    Vercel, é obrigatória.
    """
    url = os.environ.get(VARIAVEL_DE_AMBIENTE_URL_DO_BANCO)
    if url:
        engine = criar_engine_da_url(url)
    else:
        engine = criar_engine(
            Path(os.environ.get(VARIAVEL_DE_AMBIENTE_BANCO, str(CAMINHO_BANCO_PADRAO)))
        )
    na_vercel = bool(os.environ.get(VARIAVEL_DE_AMBIENTE_DA_VERCEL))
    return criar_aplicacao(
        Contexto(engine),
        senha=os.environ.get(VARIAVEL_DE_AMBIENTE_SENHA) or None,
        exigir_senha=na_vercel,
        chave_secreta=os.environ.get(VARIAVEL_DE_AMBIENTE_CHAVE_SECRETA) or None,
        cookies_seguros=na_vercel,
    )


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
