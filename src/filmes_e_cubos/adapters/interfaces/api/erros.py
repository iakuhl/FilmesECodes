"""Contrato de erro da API: toda falha vira `application/problem+json` (RFC 9457).

O corpo tem sempre os campos padronizados pela RFC (`type`, `title`,
`status`, `detail`) e mais um, `codigo`: um identificador estável do
erro, derivado do nome da exceção (`RodadaJaAbertaError` vira
`"rodada_ja_aberta"`), para que programas possam reagir a um erro
específico sem depender do texto da mensagem.

Qual status HTTP cada erro de domínio recebe é decidido em
`adapters/interfaces/erros_http.py`, compartilhado com a interface web.

Como na CLI, o tratamento acontece em um único ponto (os handlers
registrados por `registrar_tratamento_de_erros`), então nenhuma rota
precisa de `try/except`.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any, Final

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from filmes_e_cubos.adapters.interfaces.erros_http import codigo_do_erro, status_http_do_erro
from filmes_e_cubos.domain.exceptions.base import DomainError

TIPO_DE_CONTEUDO_PROBLEMA: Final = "application/problem+json"

_TITULOS: Final[dict[int, str]] = {
    HTTPStatus.BAD_REQUEST: "Requisição malformada",
    HTTPStatus.NOT_FOUND: "Não encontrado",
    HTTPStatus.METHOD_NOT_ALLOWED: "Método não permitido",
    HTTPStatus.CONFLICT: "Conflito com o estado atual",
    HTTPStatus.UNPROCESSABLE_ENTITY: "Requisição inválida",
    HTTPStatus.INTERNAL_SERVER_ERROR: "Erro interno",
}

_CODIGOS_HTTP: Final[dict[int, str]] = {
    HTTPStatus.NOT_FOUND: "recurso_nao_encontrado",
    HTTPStatus.METHOD_NOT_ALLOWED: "metodo_nao_permitido",
}

# O roteamento do Starlette preenche o detalhe com a frase padrão do HTTP,
# em inglês ("Not Found"); estas são as versões que a API devolve no lugar.
_DETALHES_HTTP_PADRAO: Final[dict[int, str]] = {
    HTTPStatus.NOT_FOUND: "Não existe nenhum recurso neste caminho.",
    HTTPStatus.METHOD_NOT_ALLOWED: "Este caminho não aceita o método HTTP usado.",
}

_logger = logging.getLogger(__name__)


def resposta_de_problema(status: int, detalhe: str, codigo: str, **extras: Any) -> JSONResponse:
    """Monta uma resposta `application/problem+json`."""
    status = int(status)
    corpo = {
        "type": "about:blank",
        "title": _TITULOS.get(status, HTTPStatus(status).phrase),
        "status": status,
        "detail": detalhe,
        "codigo": codigo,
        **extras,
    }
    return JSONResponse(corpo, status_code=status, media_type=TIPO_DE_CONTEUDO_PROBLEMA)


def registrar_tratamento_de_erros(api: FastAPI) -> None:
    """Liga cada tipo de falha ao seu tradutor para `problem+json`."""
    api.add_exception_handler(DomainError, _tratar_erro_de_dominio)
    api.add_exception_handler(RequestValidationError, _tratar_requisicao_invalida)
    api.add_exception_handler(StarletteHTTPException, _tratar_erro_http)
    api.add_exception_handler(Exception, _tratar_erro_inesperado)


# Os handlers recebem `Exception` (e não o tipo específico) porque é essa a
# assinatura que o Starlette declara para `add_exception_handler`.


async def _tratar_erro_de_dominio(_request: Request, erro: Exception) -> JSONResponse:
    assert isinstance(erro, DomainError)
    return resposta_de_problema(status_http_do_erro(erro), str(erro), codigo_do_erro(type(erro)))


async def _tratar_requisicao_invalida(_request: Request, erro: Exception) -> JSONResponse:
    assert isinstance(erro, RequestValidationError)
    erros = [
        {
            "campo": ".".join(str(parte) for parte in detalhe["loc"]),
            "mensagem": detalhe["msg"],
            "tipo": detalhe["type"],
        }
        for detalhe in erro.errors()
    ]
    return resposta_de_problema(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "A requisição tem campos ausentes, desconhecidos ou em formato inválido.",
        "requisicao_invalida",
        erros=jsonable_encoder(erros),
    )


async def _tratar_erro_http(_request: Request, erro: Exception) -> JSONResponse:
    assert isinstance(erro, StarletteHTTPException)
    detalhe = str(erro.detail)
    if detalhe == HTTPStatus(erro.status_code).phrase:
        detalhe = _DETALHES_HTTP_PADRAO.get(erro.status_code, detalhe)
    resposta = resposta_de_problema(
        erro.status_code, detalhe, _CODIGOS_HTTP.get(erro.status_code, "erro_http")
    )
    resposta.headers.update(erro.headers or {})  # ex.: `Allow` de um 405
    return resposta


async def _tratar_erro_inesperado(_request: Request, erro: Exception) -> JSONResponse:
    _logger.exception("Erro inesperado ao atender a requisição", exc_info=erro)
    return resposta_de_problema(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "O servidor encontrou um erro inesperado.",
        "erro_interno",
    )
