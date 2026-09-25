"""Testes das rotas de indicação, democracia e sorteio."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


def _indicar(api: ApiDeTeste, rodada: Json, membro: Json, filme: Json) -> Json:
    return api.criar(
        f"/rodadas/{rodada['id']}/indicacoes", {"membro_id": membro["id"], "filme_id": filme["id"]}
    )


def test_indicacao_normal_comeca_pendente(
    api: ApiDeTeste, rodada: Json, membro: Json, filme: Json
) -> None:
    indicacao = _indicar(api, rodada, membro, filme)

    assert indicacao["tipo"] == "normal"
    assert indicacao["status"] == "pendente"
    assert indicacao["membro_id"] == membro["id"]
    assert indicacao["filme_id"] == filme["id"]
    assert api.obter(f"/rodadas/{rodada['id']}/indicacoes") == [indicacao]
    assert api.obter(f"/indicacoes/{indicacao['id']}") == indicacao


def test_membro_indica_uma_vez_por_rodada(
    api: ApiDeTeste, rodada: Json, membro: Json, indicacao: Json, outro_filme: Json
) -> None:
    resposta = api.post(
        f"/rodadas/{rodada['id']}/indicacoes",
        {"membro_id": membro["id"], "filme_id": outro_filme["id"]},
    )

    assert_problema(resposta, 409, "indicacao_duplicada")


def test_rodada_respeita_o_tamanho_do_clube(api: ApiDeTeste, filme: Json) -> None:
    clube = api.criar("/clubes", {"nome": "Dupla", "configuracao": {"tamanho_rodada": 1}})
    iano = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Iano"})
    bia = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Bia"})
    rodada = api.criar(f"/clubes/{clube['id']}/rodadas")
    _indicar(api, rodada, iano, filme)

    resposta = api.post(
        f"/rodadas/{rodada['id']}/indicacoes", {"membro_id": bia["id"], "filme_id": filme["id"]}
    )

    assert_problema(resposta, 409, "rodada_lotada")


def test_membro_inativo_nao_indica(
    api: ApiDeTeste, rodada: Json, outro_membro: Json, filme: Json
) -> None:
    api.executar(f"/membros/{outro_membro['id']}/desativar")

    resposta = api.post(
        f"/rodadas/{rodada['id']}/indicacoes",
        {"membro_id": outro_membro["id"], "filme_id": filme["id"]},
    )

    assert_problema(resposta, 409, "membro_inativo")


def test_filme_inexistente_e_404(api: ApiDeTeste, rodada: Json, membro: Json) -> None:
    resposta = api.post(
        f"/rodadas/{rodada['id']}/indicacoes", {"membro_id": membro["id"], "filme_id": str(uuid4())}
    )

    assert_problema(resposta, 404, "entidade_nao_encontrada")


def test_nao_indica_em_rodada_encerrada(
    api: ApiDeTeste, rodada: Json, sessao: Json, outro_membro: Json, outro_filme: Json
) -> None:
    api.executar(f"/rodadas/{rodada['id']}/encerrar")

    resposta = api.post(
        f"/rodadas/{rodada['id']}/indicacoes",
        {"membro_id": outro_membro["id"], "filme_id": outro_filme["id"]},
    )

    assert_problema(resposta, 409, "rodada_ja_encerrada")


def test_democracia_nao_tem_indicador_nem_conta_na_cota(
    api: ApiDeTeste, filme: Json, outro_filme: Json
) -> None:
    clube = api.criar("/clubes", {"nome": "Solo", "configuracao": {"tamanho_rodada": 1}})
    iano = api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Iano"})
    rodada = api.criar(f"/clubes/{clube['id']}/rodadas")
    _indicar(api, rodada, iano, filme)

    democracia = api.criar(
        f"/clubes/{clube['id']}/indicacoes-democracia", {"filme_id": outro_filme["id"]}
    )

    assert democracia["tipo"] == "democracia"
    assert democracia["membro_id"] is None
    assert democracia["rodada_id"] == rodada["id"]
    assert len(api.obter(f"/rodadas/{rodada['id']}/indicacoes")) == 2


def test_democracia_exige_rodada_aberta(api: ApiDeTeste, clube: Json, filme: Json) -> None:
    resposta = api.post(f"/clubes/{clube['id']}/indicacoes-democracia", {"filme_id": filme["id"]})

    assert_problema(resposta, 404, "entidade_nao_encontrada")


def test_democracia_em_clube_inexistente_e_404(api: ApiDeTeste, filme: Json) -> None:
    resposta = api.post(f"/clubes/{uuid4()}/indicacoes-democracia", {"filme_id": filme["id"]})

    corpo = assert_problema(resposta, 404, "entidade_nao_encontrada")
    assert "Clube" in corpo["detail"]


def test_sortear_marca_uma_pendente_como_sorteada(
    api: ApiDeTeste,
    rodada: Json,
    membro: Json,
    outro_membro: Json,
    filme: Json,
    outro_filme: Json,
) -> None:
    candidatas = {
        _indicar(api, rodada, membro, filme)["id"],
        _indicar(api, rodada, outro_membro, outro_filme)["id"],
    }

    sorteio = api.criar(f"/rodadas/{rodada['id']}/sorteios")

    assert sorteio["indicacao_sorteada_id"] in candidatas
    assert sorteio["rodada_id"] == rodada["id"]
    assert sorteio["metodo"]
    assert api.obter(f"/indicacoes/{sorteio['indicacao_sorteada_id']}")["status"] == "sorteada"
    assert api.obter(f"/rodadas/{rodada['id']}/sorteios") == [sorteio]


def test_sorteio_sem_pendentes_e_conflito(api: ApiDeTeste, rodada: Json) -> None:
    resposta = api.post(f"/rodadas/{rodada['id']}/sorteios")

    assert_problema(resposta, 409, "nenhuma_indicacao_elegivel")


def test_indicacao_inexistente_e_404(api: ApiDeTeste) -> None:
    assert_problema(api.get(f"/indicacoes/{uuid4()}"), 404, "entidade_nao_encontrada")
    assert_problema(api.get(f"/rodadas/{uuid4()}/indicacoes"), 404, "entidade_nao_encontrada")
    assert_problema(api.get(f"/rodadas/{uuid4()}/sorteios"), 404, "entidade_nao_encontrada")


def test_filme_nao_se_repete_no_clube(
    api: ApiDeTeste, clube: Json, rodada: Json, membro: Json, outro_membro: Json, filme: Json
) -> None:
    _indicar(api, rodada, membro, filme)

    repetida = api.post(
        f"/rodadas/{rodada['id']}/indicacoes",
        {"membro_id": outro_membro["id"], "filme_id": filme["id"]},
    )
    democracia = api.post(f"/clubes/{clube['id']}/indicacoes-democracia", {"filme_id": filme["id"]})

    assert_problema(repetida, 409, "filme_repetido_no_clube")
    assert_problema(democracia, 409, "filme_repetido_no_clube")
