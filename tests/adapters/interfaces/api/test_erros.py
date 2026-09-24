"""Testes do contrato de erro da API (`application/problem+json`, RFC 9457)."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import filmes_e_cubos.domain.exceptions as pacote_de_excecoes
from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.api.app import criar_api
from filmes_e_cubos.adapters.interfaces.api.erros import (
    STATUS_HTTP_POR_ERRO,
    codigo_do_erro,
    status_http_do_erro,
)
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine
from filmes_e_cubos.domain.exceptions.base import DomainError, EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaAbertaError
from tests.adapters.interfaces.api.conftest import ApiDeTeste, assert_problema


def _todas_as_excecoes_de_dominio() -> set[type[DomainError]]:
    """Toda subclasse de `DomainError` definida no pacote de exceções do domínio.

    Filtra pelo módulo para ignorar subclasses criadas por outros testes.
    """
    for modulo in pkgutil.iter_modules(pacote_de_excecoes.__path__):
        importlib.import_module(f"{pacote_de_excecoes.__name__}.{modulo.name}")
    encontradas: set[type[DomainError]] = set()
    pendentes: list[type[DomainError]] = [DomainError]
    while pendentes:
        for subclasse in pendentes.pop().__subclasses__():
            if subclasse.__module__.startswith(pacote_de_excecoes.__name__):
                encontradas.add(subclasse)
            pendentes.append(subclasse)
    return encontradas


def test_todo_erro_de_dominio_tem_status_http_decidido() -> None:
    """Um erro novo no domínio não pode cair no 422 genérico por esquecimento."""
    sem_classificacao = _todas_as_excecoes_de_dominio() - set(STATUS_HTTP_POR_ERRO)

    assert not sem_classificacao, "Classifique em api/erros.py: " + ", ".join(
        sorted(e.__name__ for e in sem_classificacao)
    )


def test_erro_nao_classificado_cai_em_422() -> None:
    class DesconhecidoDaApiError(DomainError):
        pass

    assert status_http_do_erro(DesconhecidoDaApiError("?")) == 422


def test_subclasse_herda_o_status_da_classificada() -> None:
    class RodadaAindaMaisAbertaError(RodadaJaAbertaError):
        pass

    assert status_http_do_erro(RodadaAindaMaisAbertaError("?")) == 409


@pytest.mark.parametrize(
    ("tipo", "codigo"),
    [
        (RodadaJaAbertaError, "rodada_ja_aberta"),
        (EntidadeNaoEncontradaError, "entidade_nao_encontrada"),
        (DomainError, "domain"),
    ],
)
def test_codigo_do_erro_deriva_do_nome_da_excecao(tipo: type[Exception], codigo: str) -> None:
    assert codigo_do_erro(tipo) == codigo


def test_caminho_inexistente_e_problema_404_em_portugues(api: ApiDeTeste) -> None:
    corpo = assert_problema(api.get("/nada-aqui"), 404, "recurso_nao_encontrado")

    assert corpo["detail"] == "Não existe nenhum recurso neste caminho."


def test_metodo_nao_aceito_e_problema_405_com_allow(api: ApiDeTeste) -> None:
    resposta = api.cliente.delete("/api/v1/clubes")

    corpo = assert_problema(resposta, 405, "metodo_nao_permitido")
    assert "GET" in resposta.headers["allow"]
    assert "método" in corpo["detail"]


def test_id_malformado_no_caminho_lista_o_campo(api: ApiDeTeste) -> None:
    corpo = assert_problema(api.get("/clubes/nao-e-uuid"), 422, "requisicao_invalida")

    assert corpo["erros"][0]["campo"] == "path.clube_id"


def test_json_malformado_e_problema_de_validacao(api: ApiDeTeste) -> None:
    resposta = api.cliente.post(
        "/api/v1/clubes", content=b"{nome:", headers={"content-type": "application/json"}
    )

    assert_problema(resposta, 422, "requisicao_invalida")


def test_erro_inesperado_vira_500_sem_vazar_detalhes(tmp_path: Path) -> None:
    api = criar_api(Contexto(criar_engine(tmp_path / "erro.db")))

    @api.get("/explodir")
    def explodir() -> None:
        raise RuntimeError("segredo interno")

    with TestClient(api, raise_server_exceptions=False) as cliente:
        resposta = cliente.get("/explodir")

    corpo = assert_problema(resposta, 500, "erro_interno")
    assert "segredo" not in corpo["detail"]
