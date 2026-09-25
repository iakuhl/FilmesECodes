"""Testes das rotas do catálogo de filmes."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


def test_so_o_titulo_e_obrigatorio(api: ApiDeTeste) -> None:
    filme = api.criar("/filmes", {"titulo": "Cidade de Deus"})

    assert filme["titulo"] == "Cidade de Deus"
    assert filme["ano_lancamento"] is None
    assert filme["diretor"] is None
    assert filme["identificador_externo"] is None
    assert filme["duracao_minutos"] is None


def test_cadastrar_com_todos_os_campos(api: ApiDeTeste) -> None:
    filme = api.criar(
        "/filmes",
        {
            "titulo": "Parasita",
            "ano_lancamento": 2019,
            "diretor": "Bong Joon-ho",
            "identificador_externo": "tt6751668",
        },
    )

    assert filme["ano_lancamento"] == 2019
    assert filme["diretor"] == "Bong Joon-ho"
    assert filme["identificador_externo"] == "tt6751668"


def test_listar_e_consultar(api: ApiDeTeste, filme: Json, outro_filme: Json) -> None:
    assert {f["titulo"] for f in api.obter("/filmes")} == {"Parasita", "Interestelar"}
    assert api.obter(f"/filmes/{filme['id']}") == filme


def test_titulo_em_branco_e_recusado(api: ApiDeTeste) -> None:
    assert_problema(api.post("/filmes", {"titulo": " "}), 422, "titulo_filme_obrigatorio")


def test_ano_nao_numerico_e_recusado_na_validacao(api: ApiDeTeste) -> None:
    resposta = api.post("/filmes", {"titulo": "Parasita", "ano_lancamento": "dois mil"})

    assert_problema(resposta, 422, "requisicao_invalida")


def test_filme_inexistente_e_404(api: ApiDeTeste) -> None:
    assert_problema(api.get(f"/filmes/{uuid4()}"), 404, "entidade_nao_encontrada")


def test_cadastrar_com_duracao(api: ApiDeTeste) -> None:
    filme = api.criar("/filmes", {"titulo": "Parasita", "duracao_minutos": 132})

    assert filme["duracao_minutos"] == 132


def test_definir_duracao_de_filme_ja_cadastrado(api: ApiDeTeste, filme: Json) -> None:
    atualizado = api.atualizar(f"/filmes/{filme['id']}/duracao", {"duracao_minutos": 132})

    assert atualizado["duracao_minutos"] == 132
    assert api.obter(f"/filmes/{filme['id']}")["duracao_minutos"] == 132


def test_duracao_nao_positiva_e_recusada(api: ApiDeTeste, filme: Json) -> None:
    resposta = api.put(f"/filmes/{filme['id']}/duracao", {"duracao_minutos": 0})

    assert_problema(resposta, 422, "duracao_filme_invalida")


def test_duracao_de_filme_inexistente_e_404(api: ApiDeTeste) -> None:
    resposta = api.put(f"/filmes/{uuid4()}/duracao", {"duracao_minutos": 90})

    assert_problema(resposta, 404, "entidade_nao_encontrada")
