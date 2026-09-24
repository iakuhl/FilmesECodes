"""Dependências injetadas pelo FastAPI nas rotas da API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from filmes_e_cubos.adapters.composicao import Contexto


def obter_contexto(request: Request) -> Contexto:
    """O `Contexto` que `criar_api` guardou no estado do app.

    O contexto é montado uma vez, na criação do app, e compartilhado por
    todas as requisições: repositórios e casos de uso não guardam estado
    entre chamadas — tudo o que muda vive no banco.
    """
    contexto = request.app.state.contexto
    if not isinstance(contexto, Contexto):
        raise RuntimeError("A API foi criada sem um Contexto (use `criar_api`).")
    return contexto


ContextoDep = Annotated[Contexto, Depends(obter_contexto)]
"""Anotação para receber o `Contexto` em uma rota: `contexto: ContextoDep`."""
