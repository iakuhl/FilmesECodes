"""Páginas de erro da web.

As ações (POST) não chegam aqui: recusas de negócio viram avisos na
página seguinte (`recusas_viram_avisos`). O que sobra são as páginas
que não existem — um id que não aponta nada, um endereço digitado errado
— e os defeitos do próprio servidor.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import Response

from filmes_e_cubos.adapters.interfaces.erros_http import status_http_do_erro
from filmes_e_cubos.adapters.interfaces.web.mensagens import mensagem_para_pessoas
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina
from filmes_e_cubos.domain.exceptions.base import DomainError

_logger = logging.getLogger(__name__)

_NAO_ENCONTRADA = "Não encontramos esta página."


def registrar_paginas_de_erro(web: FastAPI) -> None:
    web.add_exception_handler(DomainError, _erro_de_dominio)
    # Um id malformado no endereço é, para quem navega, uma página inexistente.
    web.add_exception_handler(RequestValidationError, _nao_encontrada)
    web.add_exception_handler(StarletteHTTPException, _erro_http)
    web.add_exception_handler(Exception, _erro_inesperado)


async def _erro_de_dominio(request: Request, erro: Exception) -> Response:
    assert isinstance(erro, DomainError)
    status = status_http_do_erro(erro)
    return pagina(request, "erro.html", status_code=status, mensagem=mensagem_para_pessoas(erro))


async def _nao_encontrada(request: Request, _erro: Exception) -> Response:
    return pagina(request, "erro.html", status_code=404, mensagem=_NAO_ENCONTRADA)


async def _erro_http(request: Request, erro: Exception) -> Response:
    assert isinstance(erro, StarletteHTTPException)
    mensagem = _NAO_ENCONTRADA if erro.status_code == 404 else str(erro.detail)
    return pagina(request, "erro.html", status_code=erro.status_code, mensagem=mensagem)


async def _erro_inesperado(request: Request, erro: Exception) -> Response:
    _logger.exception("Erro inesperado ao montar a página", exc_info=erro)
    return pagina(
        request,
        "erro.html",
        status_code=500,
        mensagem="Algo deu errado do nosso lado. Tente de novo em instantes.",
    )
