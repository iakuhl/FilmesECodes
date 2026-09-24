"""Testes das rotas de sessão."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


def test_sem_corpo_assume_todos_os_membros_ativos(
    api: ApiDeTeste, indicacao: Json, membro: Json, outro_membro: Json, clube: Json
) -> None:
    inativo = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Caio"})
    api.executar(f"/membros/{inativo['id']}/desativar")

    sessao = api.criar(f"/indicacoes/{indicacao['id']}/sessao")

    assert set(sessao["membros_presentes"]) == {membro["id"], outro_membro["id"]}
    assert sessao["data_sessao"] == date.today().isoformat()
    assert sessao["indicacao_id"] == indicacao["id"]


def test_corpo_sem_presentes_tambem_usa_a_presenca_padrao(
    api: ApiDeTeste, indicacao: Json, membro: Json
) -> None:
    sessao = api.criar(f"/indicacoes/{indicacao['id']}/sessao", {})

    assert sessao["membros_presentes"] == [membro["id"]]


def test_presentes_explicitos_tem_precedencia(
    api: ApiDeTeste, indicacao: Json, membro: Json, outro_membro: Json
) -> None:
    sessao = api.criar(
        f"/indicacoes/{indicacao['id']}/sessao", {"membros_presentes": [outro_membro["id"]]}
    )

    assert sessao["membros_presentes"] == [outro_membro["id"]]


def test_lista_vazia_registra_sessao_sem_presentes(api: ApiDeTeste, indicacao: Json) -> None:
    sessao = api.criar(f"/indicacoes/{indicacao['id']}/sessao", {"membros_presentes": []})

    assert sessao["membros_presentes"] == []


def test_registrar_marca_a_indicacao_como_assistida(
    api: ApiDeTeste, indicacao: Json, sessao: Json
) -> None:
    assert api.obter(f"/indicacoes/{indicacao['id']}")["status"] == "assistida"
    assert api.obter(f"/indicacoes/{indicacao['id']}/sessao") == sessao
    assert api.obter(f"/sessoes/{sessao['id']}") == sessao


def test_sessao_funciona_depois_do_sorteio(api: ApiDeTeste, rodada: Json, indicacao: Json) -> None:
    api.criar(f"/rodadas/{rodada['id']}/sorteios")

    api.criar(f"/indicacoes/{indicacao['id']}/sessao")


def test_nao_registra_duas_sessoes_para_a_mesma_indicacao(
    api: ApiDeTeste, indicacao: Json, sessao: Json
) -> None:
    resposta = api.post(f"/indicacoes/{indicacao['id']}/sessao")

    assert_problema(resposta, 409, "transicao_de_status_invalida")


def test_indicacao_ainda_nao_assistida_nao_tem_sessao(api: ApiDeTeste, indicacao: Json) -> None:
    resposta = api.get(f"/indicacoes/{indicacao['id']}/sessao")

    assert_problema(resposta, 404, "entidade_nao_encontrada")


def test_indicacao_ou_sessao_inexistente_e_404(api: ApiDeTeste) -> None:
    assert_problema(api.post(f"/indicacoes/{uuid4()}/sessao"), 404, "entidade_nao_encontrada")
    assert_problema(api.get(f"/sessoes/{uuid4()}"), 404, "entidade_nao_encontrada")
