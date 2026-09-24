"""Testes do contrato de erro da API (`application/problem+json`, RFC 9457).

A classificação de cada erro de domínio em status HTTP é testada em
`tests/adapters/interfaces/test_erros_http.py`.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.api.app import criar_api
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine
from tests.adapters.interfaces.api.conftest import ApiDeTeste, assert_problema


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
