"""Testes das rotas da votação do Óscar: situação, votos e confirmação da cédula."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


@dataclass(frozen=True)
class EdicaoEmVotacao:
    temporada_id: str
    categoria_id: str
    nomeacoes: list[str]
    """As duas nomeações da categoria, na ordem da cédula."""


@pytest.fixture
def edicao(
    api: ApiDeTeste, clube: Json, sessao: Json, filme: Json, outro_membro: Json
) -> EdicaoEmVotacao:
    """Iano e Bia como eleitores, e uma categoria com o mesmo filme nomeado duas vezes."""
    temporada = api.criar(f"/clubes/{clube['id']}/oscar/temporadas", {"nomeacoes_por_categoria": 2})
    categoria = api.criar(
        f"/oscar/temporadas/{temporada['id']}/categorias", {"nome": "Melhor veículo"}
    )
    api.executar(f"/oscar/temporadas/{temporada['id']}/avancar")
    nomeacoes = [
        api.criar(f"/oscar/categorias/{categoria['id']}/nomeacoes", {"filme_id": filme["id"]})["id"]
        for _ in range(2)
    ]
    api.executar(f"/oscar/temporadas/{temporada['id']}/avancar")
    return EdicaoEmVotacao(temporada["id"], categoria["id"], nomeacoes)


def _votar(api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json, *posicoes: int) -> Json:
    return api.atualizar(
        f"/oscar/categorias/{edicao.categoria_id}/votos/{membro['id']}",
        {"escolhas": [edicao.nomeacoes[posicao] for posicao in posicoes]},
    )


def _confirmar(api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json) -> Json:
    return api.executar(
        f"/oscar/temporadas/{edicao.temporada_id}/votacao/cedulas/{membro['id']}/confirmacao"
    )


def test_situacao_da_votacao_no_inicio(
    api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json, outro_membro: Json
) -> None:
    votacao = api.obter(f"/oscar/temporadas/{edicao.temporada_id}/votacao")

    assert votacao["turno"] == 1
    assert votacao["encerrada_em"] is None
    [disputa] = votacao["categorias"]
    assert disputa["categoria_id"] == edicao.categoria_id
    assert disputa["modo"] == "dupla"
    assert [c["nomeacao_id"] for c in disputa["candidatas"]] == edicao.nomeacoes
    assert [c["posicao"] for c in disputa["candidatas"]] == [1, 2]
    assert disputa["candidatas"][0]["indicado_por_membro_id"] == membro["id"]
    assert [e["nome"] for e in votacao["eleitores"]] == ["Bia", "Iano"]
    assert all(e["categorias_votadas"] == 0 and not e["confirmou"] for e in votacao["eleitores"])


def test_voto_devolve_a_cedula_sem_as_escolhas(
    api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json
) -> None:
    cedula = _votar(api, edicao, membro, 1, 0)

    assert cedula == {
        "membro_id": membro["id"],
        "turno": 1,
        "categorias_votadas": [edicao.categoria_id],
        "confirmada": False,
    }


def test_confirmacao_mostra_quem_ja_confirmou(
    api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json
) -> None:
    _votar(api, edicao, membro, 0, 1)

    confirmacao = _confirmar(api, edicao, membro)

    assert confirmacao["turno_encerrado"] is False
    eleitores = {e["nome"]: e for e in confirmacao["votacao"]["eleitores"]}
    assert eleitores["Iano"]["confirmou"] is True
    assert eleitores["Bia"]["confirmou"] is False


def test_ultima_confirmacao_termina_a_votacao(
    api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json, outro_membro: Json
) -> None:
    for eleitor in (membro, outro_membro):
        _votar(api, edicao, eleitor, 0, 1)
    _confirmar(api, edicao, membro)

    confirmacao = _confirmar(api, edicao, outro_membro)

    assert confirmacao["turno_encerrado"] is True
    assert confirmacao["votacao"]["encerrada_em"] is not None
    assert confirmacao["votacao"]["categorias"] == []


def test_empate_abre_o_turno_de_classificacao(
    api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json, outro_membro: Json
) -> None:
    _votar(api, edicao, membro, 0, 1)
    _votar(api, edicao, outro_membro, 1, 0)
    _confirmar(api, edicao, membro)

    votacao = _confirmar(api, edicao, outro_membro)["votacao"]

    assert votacao["turno"] == 2
    assert votacao["encerrada_em"] is None
    assert votacao["categorias"][0]["modo"] == "classificacao"
    assert not any(e["confirmou"] for e in votacao["eleitores"])


def test_so_os_eleitores_votam(api: ApiDeTeste, clube: Json, edicao: EdicaoEmVotacao) -> None:
    caio = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Caio"})

    resposta = api.put(
        f"/oscar/categorias/{edicao.categoria_id}/votos/{caio['id']}",
        {"escolhas": edicao.nomeacoes},
    )

    assert_problema(resposta, 409, "membro_fora_da_votacao")


def test_voto_invalido(api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json) -> None:
    resposta = api.put(
        f"/oscar/categorias/{edicao.categoria_id}/votos/{membro['id']}",
        {"escolhas": [edicao.nomeacoes[0], edicao.nomeacoes[0]]},
    )

    assert_problema(resposta, 422, "voto_invalido")


def test_confirmar_sem_votar_em_tudo(
    api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json
) -> None:
    resposta = api.post(
        f"/oscar/temporadas/{edicao.temporada_id}/votacao/cedulas/{membro['id']}/confirmacao"
    )

    assert "Melhor veículo" in assert_problema(resposta, 409, "cedula_incompleta")["detail"]


def test_cedula_confirmada_nao_muda(api: ApiDeTeste, edicao: EdicaoEmVotacao, membro: Json) -> None:
    _votar(api, edicao, membro, 0, 1)
    _confirmar(api, edicao, membro)

    resposta = api.put(
        f"/oscar/categorias/{edicao.categoria_id}/votos/{membro['id']}",
        {"escolhas": list(reversed(edicao.nomeacoes))},
    )

    assert_problema(resposta, 409, "cedula_confirmada")


def test_votacao_antes_da_fase(api: ApiDeTeste, clube: Json) -> None:
    temporada = api.criar(f"/clubes/{clube['id']}/oscar/temporadas")

    resposta = api.get(f"/oscar/temporadas/{temporada['id']}/votacao")

    assert_problema(resposta, 404, "entidade_nao_encontrada")
