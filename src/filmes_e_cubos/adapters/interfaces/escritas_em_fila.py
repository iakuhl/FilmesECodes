"""Middleware ASGI que faz as requisições que alteram dados rodarem uma de cada vez.

Por que existe: vários casos de uso seguem o padrão "lê, confere uma
regra, grava". `IndicarFilme` confere que o membro ainda não indicou na
rodada antes de gravar a indicação; `AvaliarFilme` confere que ele ainda
não avaliou a sessão. Com duas requisições simultâneas — um duplo clique
num formulário basta —, as duas podem ler o estado antigo, passar na
conferência e gravar: a regra seria violada sem que nenhuma percebesse.

O jeito "de livro" de resolver isso é uma transação por caso de uso
(*Unit of Work*). Este projeto usa SQLite, que já aceita um único
escritor por vez, e o servidor roda em um único processo: enfileirar as
escritas no próprio processo dá a cada caso de uso a atomicidade de que
ele precisa, com uma fração da complexidade. Leituras (GET, HEAD,
OPTIONS) continuam concorrentes. Se um dia o sistema rodar em vários
processos ou sobre outro banco, esta peça dá lugar a transações de
verdade — ver a ADR correspondente em docs/ARQUITETURA.md.
"""

from __future__ import annotations

import asyncio
from typing import Final

from starlette.types import ASGIApp, Receive, Scope, Send

METODOS_SEM_ESCRITA: Final = frozenset({"GET", "HEAD", "OPTIONS"})


class EscritasEmFila:
    """Deixa passar leituras livremente e enfileira todo o resto."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app
        self._trava = asyncio.Lock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in METODOS_SEM_ESCRITA:
            await self._app(scope, receive, send)
            return
        async with self._trava:
            await self._app(scope, receive, send)
