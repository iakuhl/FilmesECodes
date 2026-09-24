"""Testes das rotas de membros."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


def test_cadastrar_membro_ja_ativo(api: ApiDeTeste, clube: Json) -> None:
    membro = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Iano", "apelido": "Ianinho"})

    assert membro["nome"] == "Iano"
    assert membro["apelido"] == "Ianinho"
    assert membro["clube_id"] == clube["id"]
    assert membro["ativo"] is True
    assert membro["data_ingresso"] == date.today().isoformat()


def test_apelido_e_opcional(api: ApiDeTeste, clube: Json) -> None:
    membro = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Bia"})

    assert membro["apelido"] is None


def test_desativar_preserva_o_membro_e_o_tira_dos_ativos(
    api: ApiDeTeste, clube: Json, membro: Json, outro_membro: Json
) -> None:
    desativado = api.executar(f"/membros/{outro_membro['id']}/desativar")

    assert desativado["ativo"] is False
    todos = api.obter(f"/clubes/{clube['id']}/membros")
    ativos = api.obter(f"/clubes/{clube['id']}/membros", apenas_ativos=True)
    assert {m["nome"] for m in todos} == {"Iano", "Bia"}
    assert [m["nome"] for m in ativos] == ["Iano"]


def test_consultar_membro(api: ApiDeTeste, membro: Json) -> None:
    assert api.obter(f"/membros/{membro['id']}") == membro


def test_membros_de_outro_clube_nao_aparecem(api: ApiDeTeste, clube: Json, membro: Json) -> None:
    outro_clube = api.criar("/clubes", {"nome": "Cineclube do Bairro"})
    api.criar(f"/clubes/{outro_clube['id']}/membros", {"nome": "Duda"})

    assert [m["nome"] for m in api.obter(f"/clubes/{clube['id']}/membros")] == ["Iano"]


def test_nome_em_branco_e_recusado(api: ApiDeTeste, clube: Json) -> None:
    resposta = api.post(f"/clubes/{clube['id']}/membros", {"nome": ""})

    assert_problema(resposta, 422, "nome_membro_obrigatorio")


def test_clube_inexistente_e_404(api: ApiDeTeste) -> None:
    assert_problema(
        api.post(f"/clubes/{uuid4()}/membros", {"nome": "Iano"}), 404, "entidade_nao_encontrada"
    )
    assert_problema(api.get(f"/clubes/{uuid4()}/membros"), 404, "entidade_nao_encontrada")


def test_membro_inexistente_e_404(api: ApiDeTeste) -> None:
    assert_problema(api.get(f"/membros/{uuid4()}"), 404, "entidade_nao_encontrada")
    assert_problema(api.post(f"/membros/{uuid4()}/desativar"), 404, "entidade_nao_encontrada")
