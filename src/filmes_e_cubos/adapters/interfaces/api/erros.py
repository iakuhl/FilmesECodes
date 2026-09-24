"""Contrato de erro da API: toda falha vira `application/problem+json` (RFC 9457).

O corpo tem sempre os campos padronizados pela RFC (`type`, `title`,
`status`, `detail`) e mais um, `codigo`: um identificador estável do
erro, derivado do nome da exceção (`RodadaJaAbertaError` vira
`"rodada_ja_aberta"`), para que programas possam reagir a um erro
específico sem depender do texto da mensagem.

O domínio não classifica seus erros em "dado inválido" e "conflito com o
estado atual" — essa distinção só existe no HTTP. Por isso a
classificação mora aqui, em `STATUS_HTTP_POR_ERRO`, e é explícita para
cada erro: um teste garante que nenhuma exceção de domínio nova fique de
fora sem que alguém decida qual status ela merece.

Como na CLI, o tratamento acontece em um único ponto (os handlers
registrados por `registrar_tratamento_de_erros`), então nenhuma rota
precisa de `try/except`.
"""

from __future__ import annotations

import logging
import re
from http import HTTPStatus
from typing import Any, Final

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from filmes_e_cubos.domain.exceptions.avaliacao import (
    AvaliacaoDuplicadaError,
    EscalaAvaliacaoInvalidaError,
    NotaForaDaEscalaError,
    NotaInvalidaError,
)
from filmes_e_cubos.domain.exceptions.base import DomainError, EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.clube import (
    NomeClubeObrigatorioError,
    TamanhoRodadaInvalidoError,
)
from filmes_e_cubos.domain.exceptions.filme import TituloFilmeObrigatorioError
from filmes_e_cubos.domain.exceptions.indicacao import (
    IndicacaoDuplicadaError,
    TransicaoDeStatusInvalidaError,
)
from filmes_e_cubos.domain.exceptions.membro import MembroInativoError, NomeMembroObrigatorioError
from filmes_e_cubos.domain.exceptions.oscar import (
    CategoriaJaApuradaError,
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
    NomeacaoInvalidaError,
    NomeCategoriaObrigatorioError,
    TemporadaOscarInvalidaError,
    VencedorDemocraciaNaoInformadoError,
)
from filmes_e_cubos.domain.exceptions.rodada import (
    RodadaJaAbertaError,
    RodadaJaEncerradaError,
    RodadaLotadaError,
    RodadaNaoEncerravelError,
)
from filmes_e_cubos.domain.exceptions.sorteio import (
    IndicacaoNaoElegivelParaSorteioError,
    NenhumaIndicacaoElegivelError,
)

TIPO_DE_CONTEUDO_PROBLEMA: Final = "application/problem+json"

_NAO_ENCONTRADO: Final[tuple[type[DomainError], ...]] = (EntidadeNaoEncontradaError,)

# A requisição é válida, mas colide com o estado atual (tentar de novo não
# adianta até que o estado mude).
_CONFLITO: Final[tuple[type[DomainError], ...]] = (
    AvaliacaoDuplicadaError,
    CategoriaJaApuradaError,
    IndicacaoDuplicadaError,
    MembroInativoError,
    NenhumaIndicacaoElegivelError,
    RodadaJaAbertaError,
    RodadaJaEncerradaError,
    RodadaLotadaError,
    RodadaNaoEncerravelError,
    TemporadaOscarInvalidaError,
    TransicaoDeStatusInvalidaError,
)

# Os dados enviados violam uma regra de negócio, independentemente do estado.
_ENTRADA_INVALIDA: Final[tuple[type[DomainError], ...]] = (
    EscalaAvaliacaoInvalidaError,
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
    NomeacaoInvalidaError,
    NomeCategoriaObrigatorioError,
    NomeClubeObrigatorioError,
    NomeMembroObrigatorioError,
    NotaForaDaEscalaError,
    NotaInvalidaError,
    TamanhoRodadaInvalidoError,
    TituloFilmeObrigatorioError,
    VencedorDemocraciaNaoInformadoError,
)

# Defeito do próprio servidor: o sorteador devolveu um candidato inexistente.
# O cliente não fez nada de errado.
_FALHA_INTERNA: Final[tuple[type[DomainError], ...]] = (IndicacaoNaoElegivelParaSorteioError,)

STATUS_HTTP_POR_ERRO: Final[dict[type[DomainError], int]] = {
    **dict.fromkeys(_NAO_ENCONTRADO, HTTPStatus.NOT_FOUND),
    **dict.fromkeys(_CONFLITO, HTTPStatus.CONFLICT),
    **dict.fromkeys(_ENTRADA_INVALIDA, HTTPStatus.UNPROCESSABLE_ENTITY),
    **dict.fromkeys(_FALHA_INTERNA, HTTPStatus.INTERNAL_SERVER_ERROR),
}
"""Status HTTP de cada erro de domínio. Um erro não listado cai em 422."""

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


def status_http_do_erro(erro: DomainError) -> int:
    """O status mais específico classificado para o erro (ou 422, se nenhum)."""
    for tipo in type(erro).__mro__:
        if tipo in STATUS_HTTP_POR_ERRO:
            return STATUS_HTTP_POR_ERRO[tipo]
    return HTTPStatus.UNPROCESSABLE_ENTITY


def codigo_do_erro(tipo: type[Exception]) -> str:
    """`RodadaJaAbertaError` -> `"rodada_ja_aberta"`."""
    nome = tipo.__name__.removesuffix("Error")
    return re.sub(r"(?<!^)(?=[A-Z])", "_", nome).lower()


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
