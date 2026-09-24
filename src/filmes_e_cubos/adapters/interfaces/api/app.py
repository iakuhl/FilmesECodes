"""Montagem do app FastAPI da API a partir das rotas de cada grupo de recursos."""

from __future__ import annotations

from typing import Any, Final

from fastapi import APIRouter, FastAPI

from filmes_e_cubos import __version__
from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.api.erros import (
    TIPO_DE_CONTEUDO_PROBLEMA,
    registrar_tratamento_de_erros,
)
from filmes_e_cubos.adapters.interfaces.api.esquemas import Problema, SaudeSaida
from filmes_e_cubos.adapters.interfaces.api.rotas import (
    avaliacoes,
    clubes,
    filmes,
    indicacoes,
    membros,
    oscar,
    rodadas,
    sessoes,
)

_ROTEADORES: Final[tuple[APIRouter, ...]] = (
    clubes.roteador,
    membros.roteador,
    filmes.roteador,
    rodadas.roteador,
    indicacoes.roteador,
    sessoes.roteador,
    avaliacoes.roteador,
    oscar.roteador,
)


def _resposta_de_erro(descricao: str) -> dict[str, Any]:
    return {
        "description": descricao,
        "content": {
            TIPO_DE_CONTEUDO_PROBLEMA: {
                "schema": {"$ref": "#/components/schemas/Problema"},
            }
        },
    }


_RESPOSTAS_DE_ERRO: Final[dict[int | str, dict[str, Any]]] = {
    404: _resposta_de_erro("Recurso (ou entidade referenciada) não encontrado."),
    409: _resposta_de_erro("A ação colide com o estado atual (ex.: rodada já aberta)."),
    422: _resposta_de_erro("Dados ausentes, malformados ou que violam uma regra de negócio."),
}

_DESCRICAO: Final = """
API do clube de cinema **Filmes e Cubos**: membros, catálogo de filmes, rodadas de
indicação, sorteios, sessões, avaliações e o Óscar anual do clube.

Toda resposta de erro segue a RFC 9457 (`application/problem+json`), com um campo
extra, `codigo`, que identifica o erro de forma estável. Veja docs/API.md no
repositório para as convenções completas.
"""


def criar_api(contexto: Contexto) -> FastAPI:
    """Cria a API sobre um `Contexto` já montado (banco, relógio, sorteador)."""
    api = FastAPI(
        title="Filmes e Cubos",
        version=__version__,
        description=_DESCRICAO,
        responses=_RESPOSTAS_DE_ERRO,
    )
    api.state.contexto = contexto
    registrar_tratamento_de_erros(api)

    api.include_router(_roteador_de_saude())
    for roteador in _ROTEADORES:
        api.include_router(roteador)

    _registrar_esquema_de_problema(api)
    return api


def _roteador_de_saude() -> APIRouter:
    roteador = APIRouter(tags=["infraestrutura"])

    @roteador.get("/saude", summary="Indica que a API está no ar")
    def saude() -> SaudeSaida:
        return SaudeSaida(status="ok", versao=__version__)

    return roteador


def _registrar_esquema_de_problema(api: FastAPI) -> None:
    """Inclui o esquema `Problema` no OpenAPI, referenciado pelas respostas de erro.

    Nenhuma rota devolve `Problema` como resposta de sucesso, então o
    FastAPI não o registraria sozinho — e as referências de
    `_RESPOSTAS_DE_ERRO` ficariam apontando para o vazio.
    """
    gerar_openapi_original = api.openapi

    def gerar_openapi() -> dict[str, Any]:
        if api.openapi_schema is None:
            esquema = gerar_openapi_original()
            componentes = esquema.setdefault("components", {}).setdefault("schemas", {})
            componentes["Problema"] = Problema.model_json_schema(
                ref_template="#/components/schemas/{model}"
            )
            api.openapi_schema = esquema
        return api.openapi_schema

    api.openapi = gerar_openapi  # type: ignore[method-assign]
