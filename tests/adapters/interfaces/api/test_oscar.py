"""Testes das rotas do Óscar do Filmes e Cubos."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema

ANO = date.today().year


@pytest.fixture
def temporada(api: ApiDeTeste, clube: Json) -> Json:
    return api.criar(f"/clubes/{clube['id']}/oscar/temporadas")


@pytest.fixture
def categoria(api: ApiDeTeste, temporada: Json) -> Json:
    return api.criar(f"/oscar/temporadas/{temporada['id']}/categorias", {"nome": "Melhor veículo"})


@pytest.fixture
def filme_assistido(api: ApiDeTeste, filme: Json, sessao: Json) -> Json:
    """Um filme com sessão registrada hoje — requisito para ser nomeado no ano corrente."""
    return filme


def _nomear(api: ApiDeTeste, categoria: Json, filme: Json) -> Json:
    return api.criar(f"/oscar/categorias/{categoria['id']}/nomeacoes", {"filme_id": filme["id"]})


def _apurar(api: ApiDeTeste, categoria: Json, nomeacao: Json, **extras: str) -> Json:
    return api.criar(
        f"/oscar/categorias/{categoria['id']}/apuracao",
        {"nomeacao_vencedora_id": nomeacao["id"], **extras},
    )


def test_temporada_sem_corpo_usa_ano_corrente_e_nome_padrao(
    api: ApiDeTeste, clube: Json, temporada: Json
) -> None:
    assert temporada["ano"] == ANO
    assert temporada["nome"] == f"Óscar do Filmes e Cubos {ANO}"
    assert temporada["status"] == "em_preparacao"
    assert temporada["clube_id"] == clube["id"]
    assert api.obter(f"/clubes/{clube['id']}/oscar/temporadas") == [temporada]
    assert api.obter(f"/oscar/temporadas/{temporada['id']}") == temporada


def test_temporada_com_ano_e_nome_explicitos(api: ApiDeTeste, clube: Json) -> None:
    temporada = api.criar(
        f"/clubes/{clube['id']}/oscar/temporadas", {"ano": 2020, "nome": "Óscar da Pandemia"}
    )

    assert temporada["ano"] == 2020
    assert temporada["nome"] == "Óscar da Pandemia"


def test_categoria_e_variavel_por_padrao(api: ApiDeTeste, temporada: Json, categoria: Json) -> None:
    assert categoria["tipo"] == "variavel"
    assert categoria["descricao"] is None
    assert api.obter(f"/oscar/temporadas/{temporada['id']}/categorias") == [categoria]
    assert api.obter(f"/oscar/categorias/{categoria['id']}") == categoria


def test_categoria_fixa_com_descricao(api: ApiDeTeste, temporada: Json) -> None:
    categoria = api.criar(
        f"/oscar/temporadas/{temporada['id']}/categorias",
        {"nome": "Melhor filme", "tipo": "fixa", "descricao": "O melhor do ano"},
    )

    assert categoria["tipo"] == "fixa"
    assert categoria["descricao"] == "O melhor do ano"


def test_tipo_de_categoria_desconhecido_e_recusado(api: ApiDeTeste, temporada: Json) -> None:
    resposta = api.post(
        f"/oscar/temporadas/{temporada['id']}/categorias", {"nome": "Torta", "tipo": "outra"}
    )

    assert_problema(resposta, 422, "requisicao_invalida")


def test_categoria_sem_nome_e_recusada(api: ApiDeTeste, temporada: Json) -> None:
    resposta = api.post(f"/oscar/temporadas/{temporada['id']}/categorias", {"nome": ""})

    assert_problema(resposta, 422, "nome_categoria_obrigatorio")


def test_nao_nomeia_filme_que_o_clube_nao_assistiu(
    api: ApiDeTeste, categoria: Json, filme: Json
) -> None:
    resposta = api.post(f"/oscar/categorias/{categoria['id']}/nomeacoes", {"filme_id": filme["id"]})

    assert_problema(resposta, 422, "filme_nao_assistido")


def test_nao_nomeia_filme_assistido_fora_do_ano_da_temporada(
    api: ApiDeTeste, clube: Json, filme_assistido: Json
) -> None:
    antiga = api.criar(f"/clubes/{clube['id']}/oscar/temporadas", {"ano": ANO - 1})
    categoria = api.criar(f"/oscar/temporadas/{antiga['id']}/categorias", {"nome": "Pior criança"})

    resposta = api.post(
        f"/oscar/categorias/{categoria['id']}/nomeacoes", {"filme_id": filme_assistido["id"]}
    )

    assert_problema(resposta, 422, "filme_nao_assistido_no_ano_da_temporada")


def test_nomeacao_herda_quem_indicou_o_filme(
    api: ApiDeTeste, categoria: Json, filme_assistido: Json, membro: Json
) -> None:
    nomeacao = _nomear(api, categoria, filme_assistido)

    assert nomeacao["indicado_por_membro_id"] == membro["id"]
    assert api.obter(f"/oscar/categorias/{categoria['id']}/nomeacoes") == [nomeacao]
    assert api.obter(f"/oscar/nomeacoes/{nomeacao['id']}") == nomeacao


def test_apuracao_premia_quem_indicou_o_filme_vencedor(
    api: ApiDeTeste, categoria: Json, filme_assistido: Json, membro: Json
) -> None:
    nomeacao = _nomear(api, categoria, filme_assistido)

    trofeu = _apurar(api, categoria, nomeacao)

    assert trofeu["membro_vencedor_id"] == membro["id"]
    assert trofeu["nomeacao_vencedora_id"] == nomeacao["id"]
    assert trofeu["data_apuracao"] == date.today().isoformat()
    assert api.obter(f"/oscar/categorias/{categoria['id']}/trofeu") == trofeu


def test_vencedora_precisa_concorrer_na_categoria(
    api: ApiDeTeste, temporada: Json, categoria: Json, filme_assistido: Json
) -> None:
    _nomear(api, categoria, filme_assistido)
    outra = api.criar(f"/oscar/temporadas/{temporada['id']}/categorias", {"nome": "Pior criança"})
    de_outra_categoria = _nomear(api, outra, filme_assistido)

    resposta = api.post(
        f"/oscar/categorias/{categoria['id']}/apuracao",
        {"nomeacao_vencedora_id": de_outra_categoria["id"]},
    )

    assert_problema(resposta, 422, "nomeacao_invalida")


def test_categoria_se_apura_uma_vez_so(
    api: ApiDeTeste, categoria: Json, filme_assistido: Json
) -> None:
    nomeacao = _nomear(api, categoria, filme_assistido)
    _apurar(api, categoria, nomeacao)

    resposta = api.post(
        f"/oscar/categorias/{categoria['id']}/apuracao", {"nomeacao_vencedora_id": nomeacao["id"]}
    )

    assert_problema(resposta, 409, "categoria_ja_apurada")


def test_categoria_sem_nomeacoes_nao_se_apura(api: ApiDeTeste, categoria: Json) -> None:
    resposta = api.post(
        f"/oscar/categorias/{categoria['id']}/apuracao", {"nomeacao_vencedora_id": str(uuid4())}
    )

    assert_problema(resposta, 404, "entidade_nao_encontrada")


def test_vencedor_democracia_exige_a_escolha_do_grupo(
    api: ApiDeTeste, clube: Json, rodada: Json, categoria: Json, outro_filme: Json, membro: Json
) -> None:
    democracia = api.criar(
        f"/clubes/{clube['id']}/indicacoes-democracia", {"filme_id": outro_filme["id"]}
    )
    api.criar(f"/indicacoes/{democracia['id']}/sessao")
    nomeacao = _nomear(api, categoria, outro_filme)
    assert nomeacao["indicado_por_membro_id"] is None

    sem_escolha = api.post(
        f"/oscar/categorias/{categoria['id']}/apuracao", {"nomeacao_vencedora_id": nomeacao["id"]}
    )
    assert_problema(sem_escolha, 422, "vencedor_democracia_nao_informado")

    trofeu = _apurar(api, categoria, nomeacao, membro_vencedor_id=membro["id"])
    assert trofeu["membro_vencedor_id"] == membro["id"]


def test_categoria_nao_apurada_nao_tem_trofeu(api: ApiDeTeste, categoria: Json) -> None:
    resposta = api.get(f"/oscar/categorias/{categoria['id']}/trofeu")

    assert_problema(resposta, 404, "entidade_nao_encontrada")


def test_recursos_inexistentes_sao_404(api: ApiDeTeste) -> None:
    for caminho in (
        f"/clubes/{uuid4()}/oscar/temporadas",
        f"/oscar/temporadas/{uuid4()}",
        f"/oscar/temporadas/{uuid4()}/categorias",
        f"/oscar/categorias/{uuid4()}",
        f"/oscar/categorias/{uuid4()}/nomeacoes",
        f"/oscar/categorias/{uuid4()}/trofeu",
        f"/oscar/nomeacoes/{uuid4()}",
    ):
        assert_problema(api.get(caminho), 404, "entidade_nao_encontrada")
