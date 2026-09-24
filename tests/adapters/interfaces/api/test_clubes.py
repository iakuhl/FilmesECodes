"""Testes das rotas de clubes."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


def test_clube_sem_configuracao_usa_o_padrao_do_dominio(api: ApiDeTeste) -> None:
    clube = api.criar("/clubes", {"nome": "Filmes e Cubos"})

    assert clube["nome"] == "Filmes e Cubos"
    assert clube["configuracao"] == {
        "tamanho_rodada": 5,
        "escala_avaliacao": {"nota_minima": "0.5", "nota_maxima": "5.0", "passo": "0.5"},
    }


def test_configuracao_parcial_completa_o_resto_com_o_padrao(api: ApiDeTeste) -> None:
    clube = api.criar("/clubes", {"nome": "Trio", "configuracao": {"tamanho_rodada": 3}})

    assert clube["configuracao"]["tamanho_rodada"] == 3
    assert clube["configuracao"]["escala_avaliacao"]["nota_maxima"] == "5.0"


def test_escala_aceita_numeros_e_devolve_texto_exato(api: ApiDeTeste) -> None:
    clube = api.criar(
        "/clubes",
        {
            "nome": "Notas de 1 a 10",
            "configuracao": {"escala_avaliacao": {"nota_minima": 1, "nota_maxima": 10, "passo": 1}},
        },
    )

    assert clube["configuracao"]["escala_avaliacao"] == {
        "nota_minima": "1",
        "nota_maxima": "10",
        "passo": "1",
    }


def test_nome_em_branco_e_recusado_pelo_dominio(api: ApiDeTeste) -> None:
    resposta = api.post("/clubes", {"nome": "   "})

    assert_problema(resposta, 422, "nome_clube_obrigatorio")


def test_tamanho_de_rodada_invalido_e_recusado(api: ApiDeTeste) -> None:
    resposta = api.post("/clubes", {"nome": "Vazio", "configuracao": {"tamanho_rodada": 0}})

    assert_problema(resposta, 422, "tamanho_rodada_invalido")


def test_escala_incoerente_e_recusada(api: ApiDeTeste) -> None:
    resposta = api.post(
        "/clubes",
        {
            "nome": "Torto",
            "configuracao": {"escala_avaliacao": {"nota_minima": 5, "nota_maxima": 1}},
        },
    )

    assert_problema(resposta, 422, "escala_avaliacao_invalida")


def test_campo_desconhecido_e_recusado(api: ApiDeTeste) -> None:
    resposta = api.post("/clubes", {"nome": "Filmes e Cubos", "apelido": "FeC"})

    corpo = assert_problema(resposta, 422, "requisicao_invalida")

    assert corpo["erros"][0]["campo"] == "body.apelido"


def test_listar_e_consultar(api: ApiDeTeste, clube: Json) -> None:
    outro = api.criar("/clubes", {"nome": "Cineclube do Bairro"})

    assert {c["id"] for c in api.obter("/clubes")} == {clube["id"], outro["id"]}
    assert api.obter(f"/clubes/{clube['id']}") == clube


def test_clube_inexistente_e_404(api: ApiDeTeste) -> None:
    corpo = assert_problema(api.get(f"/clubes/{uuid4()}"), 404, "entidade_nao_encontrada")

    assert "não encontrado" in corpo["detail"]
