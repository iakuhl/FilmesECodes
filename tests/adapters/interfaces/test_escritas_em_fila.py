"""Testes do middleware `EscritasEmFila`.

Usa um app ASGI mínimo que mede quantas requisições estão em andamento
ao mesmo tempo. Disparando várias requisições simultâneas, dá para ver
se o middleware enfileira as escritas e deixa as leituras correrem
juntas — sem depender de corridas reais no banco, que seriam
intermitentes demais para um teste.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx2 import ASGITransport, AsyncClient
from starlette.types import Receive, Scope, Send

from filmes_e_cubos.adapters.interfaces.escritas_em_fila import EscritasEmFila

SIMULTANEAS = 5


class AppQueMedeConcorrencia:
    def __init__(self) -> None:
        self.em_andamento = 0
        self.maximo = 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.em_andamento += 1
        self.maximo = max(self.maximo, self.em_andamento)
        await asyncio.sleep(0.02)  # dá tempo das outras requisições chegarem
        self.em_andamento -= 1
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})


def _maximo_simultaneo(metodo: str) -> int:
    medidor = AppQueMedeConcorrencia()

    async def disparar() -> None:
        transporte = ASGITransport(app=EscritasEmFila(medidor))
        async with AsyncClient(transport=transporte, base_url="http://teste") as cliente:
            await asyncio.gather(
                *(cliente.request(metodo, "/qualquer") for _ in range(SIMULTANEAS))
            )

    asyncio.run(disparar())
    return medidor.maximo


@pytest.mark.parametrize("metodo", ["POST", "PUT", "PATCH", "DELETE"])
def test_escritas_rodam_uma_de_cada_vez(metodo: str) -> None:
    assert _maximo_simultaneo(metodo) == 1


@pytest.mark.parametrize("metodo", ["GET", "HEAD", "OPTIONS"])
def test_leituras_rodam_juntas(metodo: str) -> None:
    assert _maximo_simultaneo(metodo) == SIMULTANEAS
