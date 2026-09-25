"""Testes das rotas de avaliação."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from httpx2 import Response

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


def _avaliar(api: ApiDeTeste, sessao: Json, membro: Json, **campos: Any) -> Response:
    return api.post(f"/sessoes/{sessao['id']}/avaliacoes", {"membro_id": membro["id"], **campos})


def test_registrar_nota(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    resposta = _avaliar(api, sessao, membro, nota="4.5", comentario="Obra-prima")

    assert resposta.status_code == 201, resposta.text
    avaliacao = resposta.json()
    assert avaliacao["status"] == "nota_registrada"
    assert avaliacao["nota"] == "4.5"
    assert avaliacao["comentario"] == "Obra-prima"
    assert api.obter(f"/sessoes/{sessao['id']}/avaliacoes") == [avaliacao]


def test_nota_pode_vir_como_numero(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    resposta = _avaliar(api, sessao, membro, nota=3.5)

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["nota"] == "3.5"


def test_nota_nula_registra_dorminhoco(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    resposta = _avaliar(api, sessao, membro, nota=None)

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["status"] == "dorminhoco"
    assert resposta.json()["nota"] is None


def test_nota_ausente_e_recusada_para_ninguem_virar_dorminhoco_por_engano(
    api: ApiDeTeste, sessao: Json, membro: Json
) -> None:
    corpo = assert_problema(_avaliar(api, sessao, membro), 422, "requisicao_invalida")

    assert corpo["erros"][0]["campo"] == "body.nota"
    assert api.obter(f"/sessoes/{sessao['id']}/avaliacoes") == []


def test_nota_fora_da_escala_e_recusada(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    assert_problema(_avaliar(api, sessao, membro, nota=7), 422, "nota_fora_da_escala")


def test_nota_fora_do_passo_e_recusada(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    corpo = assert_problema(_avaliar(api, sessao, membro, nota="4.3"), 422, "nota_fora_da_escala")

    assert "passo" in corpo["detail"]


def test_nota_nao_positiva_e_recusada(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    assert_problema(_avaliar(api, sessao, membro, nota=0), 422, "nota_invalida")


def test_membro_avalia_uma_vez_so(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    _avaliar(api, sessao, membro, nota=5)

    assert_problema(_avaliar(api, sessao, membro, nota=None), 409, "avaliacao_duplicada")


def test_vale_a_escala_do_clube_dono_da_sessao(api: ApiDeTeste, clube: Json) -> None:
    """Com dois clubes, a escala certa vem da sessão — nenhum id de clube é pedido."""
    de_um_a_dez = api.criar(
        "/clubes",
        {
            "nome": "Notas de 1 a 10",
            "configuracao": {"escala_avaliacao": {"nota_minima": 1, "nota_maxima": 10, "passo": 1}},
        },
    )
    membro = api.criar(f"/clubes/{de_um_a_dez['id']}/membros", {"nome": "Duda"})
    filme = api.criar("/filmes", {"titulo": "Aftersun"})
    rodada = api.criar(f"/clubes/{de_um_a_dez['id']}/rodadas")
    indicacao = api.criar(
        f"/rodadas/{rodada['id']}/indicacoes", {"membro_id": membro["id"], "filme_id": filme["id"]}
    )
    sessao = api.criar(f"/indicacoes/{indicacao['id']}/sessao")

    resposta = _avaliar(api, sessao, membro, nota=7)

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["nota"] == "7"


def test_sessao_ou_membro_inexistente_e_404(api: ApiDeTeste, sessao: Json, membro: Json) -> None:
    fantasma = {"id": str(uuid4())}

    assert_problema(_avaliar(api, fantasma, membro, nota=4), 404, "entidade_nao_encontrada")
    assert_problema(_avaliar(api, sessao, fantasma, nota=4), 404, "entidade_nao_encontrada")
    assert_problema(api.get(f"/sessoes/{uuid4()}/avaliacoes"), 404, "entidade_nao_encontrada")


def test_quem_nao_esteve_na_sessao_nao_avalia(api: ApiDeTeste, clube: Json, sessao: Json) -> None:
    chegou_depois = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Caio"})

    resposta = _avaliar(api, sessao, chegou_depois, nota=4)

    assert_problema(resposta, 409, "membro_ausente_na_sessao")


def test_sessao_expoe_a_media_como_fracao_e_em_estrelas(
    api: ApiDeTeste, indicacao: Json, membro: Json, outro_membro: Json
) -> None:
    sessao = api.criar(f"/indicacoes/{indicacao['id']}/sessao")
    assert sessao["media_das_notas"] is None

    _avaliar(api, sessao, membro, nota="4")
    _avaliar(api, sessao, outro_membro, nota="3.5")

    media = api.obter(f"/sessoes/{sessao['id']}")["media_das_notas"]
    assert media == {"soma_das_notas": "7.5", "quantidade_de_notas": 2, "estrelas": "★★★¾"}
