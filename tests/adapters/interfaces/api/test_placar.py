"""Testes do envio do placar pela API (decisão 27 de docs/PENDENCIAS.md)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.erros_http import status_http_do_erro
from filmes_e_cubos.adapters.interfaces.servidor import criar_aplicacao
from filmes_e_cubos.domain.exceptions.email import (
    EnvioDeEmailIndisponivelError,
    FalhaNoEnvioDeEmailError,
)
from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema
from tests.application.fakes.enviador_de_email_fake import EnviadorDeEmailFake


@pytest.fixture
def correio() -> EnviadorDeEmailFake:
    return EnviadorDeEmailFake()


@pytest.fixture
def api(engine_de_teste: Engine, correio: EnviadorDeEmailFake) -> Iterator[ApiDeTeste]:
    """A API com um correio que guarda as mensagens em vez de enviá-las."""
    with TestClient(criar_aplicacao(Contexto(engine_de_teste, enviador=correio))) as cliente:
        yield ApiDeTeste(cliente)


@pytest.fixture
def temporada(api: ApiDeTeste, clube: Json, sessao: Json, filme: Json, membro: Json) -> Json:
    """Uma edição em votação, com Iano como único eleitor e uma categoria."""
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
    return temporada


def _confirmar(api: ApiDeTeste, temporada: Json, membro: Json) -> None:
    api.executar(f"/oscar/temporadas/{temporada['id']}/votacao/cedulas/{membro['id']}/confirmacao")


def test_placar_sai_por_email_e_nao_aparece_na_resposta(
    api: ApiDeTeste, temporada: Json, membro: Json, correio: EnviadorDeEmailFake
) -> None:
    _confirmar(api, temporada, membro)

    resposta = api.executar(
        f"/oscar/temporadas/{temporada['id']}/placar/envios",
        {"destinatario": "cerimonia@clube.com"},
    )

    assert resposta == {"destinatario": "cerimonia@clube.com"}
    [mensagem] = correio.enviadas
    assert "Parasita — indicado por Iano" in mensagem.corpo


def test_placar_antes_do_fim_da_votacao(api: ApiDeTeste, temporada: Json) -> None:
    resposta = api.post(
        f"/oscar/temporadas/{temporada['id']}/placar/envios", {"destinatario": "a@b.com"}
    )

    assert_problema(resposta, 409, "votacao_em_andamento")


def test_endereco_invalido(api: ApiDeTeste, temporada: Json, membro: Json) -> None:
    _confirmar(api, temporada, membro)

    resposta = api.post(
        f"/oscar/temporadas/{temporada['id']}/placar/envios", {"destinatario": "cerimonia"}
    )

    assert_problema(resposta, 422, "endereco_de_email_invalido")


def test_servidor_de_email_desligado_ou_fora_do_ar_tem_status_proprio() -> None:
    assert status_http_do_erro(EnvioDeEmailIndisponivelError("desligado")) == 503
    assert status_http_do_erro(FalhaNoEnvioDeEmailError("fora do ar")) == 502
