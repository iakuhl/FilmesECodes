"""Testes do registro dos vencedores pela API (decisão 29 de docs/PENDENCIAS.md)."""

from __future__ import annotations

from datetime import date

import pytest

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


@pytest.fixture
def categoria(api: ApiDeTeste, clube: Json, sessao: Json, filme: Json, membro: Json) -> Json:
    """Uma categoria cuja votação já terminou: Iano, único eleitor, votou e confirmou."""
    temporada = api.criar(f"/clubes/{clube['id']}/oscar/temporadas", {"nomeacoes_por_categoria": 2})
    categoria = api.criar(f"/oscar/temporadas/{temporada['id']}/categorias", {"nome": "Veículo"})
    api.executar(f"/oscar/temporadas/{temporada['id']}/avancar")
    nomeacoes = [
        api.criar(f"/oscar/categorias/{categoria['id']}/nomeacoes", {"filme_id": filme["id"]})
        for _ in range(2)
    ]
    api.executar(f"/oscar/temporadas/{temporada['id']}/avancar")
    api.atualizar(
        f"/oscar/categorias/{categoria['id']}/votos/{membro['id']}",
        {"escolhas": [nomeacao["id"] for nomeacao in nomeacoes]},
    )
    api.executar(f"/oscar/temporadas/{temporada['id']}/votacao/cedulas/{membro['id']}/confirmacao")
    return {**categoria, "nomeacoes": nomeacoes, "temporada": temporada}


def test_trofeu_vai_para_quem_indicou(api: ApiDeTeste, categoria: Json, membro: Json) -> None:
    vencedora = categoria["nomeacoes"][0]

    trofeu = api.criar(
        f"/oscar/categorias/{categoria['id']}/trofeu", {"nomeacao_id": vencedora["id"]}
    )

    assert trofeu["membro_vencedor_id"] == membro["id"]
    assert trofeu["nomeacao_vencedora_id"] == vencedora["id"]
    assert trofeu["data_apuracao"] == date.today().isoformat()
    assert api.obter(f"/oscar/categorias/{categoria['id']}/trofeu") == trofeu
    temporada = api.executar(f"/oscar/temporadas/{categoria['temporada']['id']}/avancar")
    assert temporada["status"] == "apurada"


def test_empate_absoluto(api: ApiDeTeste, categoria: Json, outro_membro: Json) -> None:
    sem_escolha = api.post(f"/oscar/categorias/{categoria['id']}/trofeu", {})
    trofeu = api.criar(
        f"/oscar/categorias/{categoria['id']}/trofeu", {"membro_escolhido_id": outro_membro["id"]}
    )

    assert_problema(sem_escolha, 422, "escolha_do_grupo_necessaria")
    assert trofeu["nomeacao_vencedora_id"] is None
    assert trofeu["membro_vencedor_id"] == outro_membro["id"]


def test_escolhido_de_outro_clube(api: ApiDeTeste, categoria: Json) -> None:
    outro = api.criar("/clubes", {"nome": "Cine Vizinhança"})
    duda = api.criar(f"/clubes/{outro['id']}/membros", {"nome": "Duda"})

    resposta = api.post(
        f"/oscar/categorias/{categoria['id']}/trofeu", {"membro_escolhido_id": duda["id"]}
    )

    assert_problema(resposta, 422, "membro_de_outro_clube")


def test_vencedor_nao_muda(api: ApiDeTeste, categoria: Json) -> None:
    corpo = {"nomeacao_id": categoria["nomeacoes"][0]["id"]}
    api.criar(f"/oscar/categorias/{categoria['id']}/trofeu", corpo)

    assert_problema(
        api.post(f"/oscar/categorias/{categoria['id']}/trofeu", corpo), 409, "categoria_ja_apurada"
    )
