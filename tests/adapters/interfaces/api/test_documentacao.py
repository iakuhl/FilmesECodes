"""Testes da documentação OpenAPI e da rota de saúde."""

from __future__ import annotations

from filmes_e_cubos import __version__
from tests.adapters.interfaces.api.conftest import ApiDeTeste


def test_saude(api: ApiDeTeste) -> None:
    assert api.obter("/saude") == {"status": "ok", "versao": __version__}


def test_openapi_descreve_os_recursos_e_os_erros(api: ApiDeTeste) -> None:
    documento = api.obter("/openapi.json")

    caminhos = documento["paths"]
    for caminho in (
        "/clubes",
        "/clubes/{clube_id}/membros",
        "/rodadas/{rodada_id}/indicacoes",
        "/indicacoes/{indicacao_id}/sessao",
        "/sessoes/{sessao_id}/avaliacoes",
        "/oscar/categorias/{categoria_id}/apuracao",
    ):
        assert caminho in caminhos
    assert "Problema" in documento["components"]["schemas"]
    respostas = caminhos["/clubes/{clube_id}"]["get"]["responses"]
    assert set(respostas) >= {"200", "404", "409", "422"}
    assert "application/problem+json" in respostas["404"]["content"]


def test_documentacao_interativa_aponta_para_o_openapi_da_api(api: ApiDeTeste) -> None:
    resposta = api.get("/docs")

    assert resposta.status_code == 200
    assert "/api/v1/openapi.json" in resposta.text


def test_raiz_do_servidor_leva_a_documentacao(api: ApiDeTeste) -> None:
    resposta = api.cliente.get("/", follow_redirects=False)

    assert resposta.status_code == 307
    assert resposta.headers["location"] == "/api/v1/docs"
