"""Testes da proteção por senha do clube (decisão 35 de docs/PENDENCIAS.md)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.servidor import criar_aplicacao
from tests.adapters.interfaces.web.conftest import WebDeTeste, avisos

SENHA = "pipoca-com-manteiga"


@pytest.fixture
def protegida(engine_de_teste: Engine) -> Iterator[WebDeTeste]:
    aplicacao = criar_aplicacao(Contexto(engine_de_teste), senha=SENHA)
    with TestClient(aplicacao) as cliente:
        yield WebDeTeste(cliente)


def test_sem_senha_configurada_o_site_abre_direto(web: WebDeTeste) -> None:
    assert web.abrir("/").select_one("h1") is not None


def test_com_senha_quem_nao_entrou_vai_para_a_entrada(protegida: WebDeTeste) -> None:
    resposta = protegida.cliente.get("/clubes/x?aba=1", follow_redirects=False)

    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/entrar?proximo=/clubes/x%3Faba%3D1"


def test_senha_errada_e_recusada(protegida: WebDeTeste) -> None:
    resposta = protegida.enviar("/entrar", senha="errada", proximo="/")

    assert resposta.status_code == 401
    assert "Senha incorreta" in resposta.text
    assert protegida.cliente.get("/", follow_redirects=False).status_code == 303


def test_senha_certa_abre_o_site_ate_sair(protegida: WebDeTeste) -> None:
    resposta = protegida.enviar("/entrar", senha=SENHA, proximo="/")
    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/"

    pagina = protegida.abrir("/")
    assert pagina.select_one("form[action='/sair']") is not None

    protegida.agir("/sair")
    assert protegida.cliente.get("/", follow_redirects=False).status_code == 303


def test_entrada_so_volta_para_paginas_do_proprio_site(protegida: WebDeTeste) -> None:
    resposta = protegida.enviar("/entrar", senha=SENHA, proximo="//outro.site/golpe")

    assert resposta.headers["location"] == "/"


def test_api_pede_a_senha_no_cabecalho(protegida: WebDeTeste) -> None:
    sem_senha = protegida.cliente.get("/api/v1/clubes")
    com_senha = protegida.cliente.get(
        "/api/v1/clubes", headers={"Authorization": f"Bearer {SENHA}"}
    )

    assert sem_senha.status_code == 401
    assert sem_senha.headers["content-type"] == "application/problem+json"
    assert sem_senha.json()["codigo"] == "nao_autenticado"
    assert sem_senha.headers["www-authenticate"] == "Bearer"
    assert com_senha.status_code == 200


def test_quem_entrou_no_site_usa_a_api_pelo_navegador(protegida: WebDeTeste) -> None:
    protegida.enviar("/entrar", senha=SENHA, proximo="/")

    assert protegida.cliente.get("/api/v1/clubes").status_code == 200


def test_saude_e_visual_ficam_livres(protegida: WebDeTeste) -> None:
    assert protegida.cliente.get("/api/v1/saude").status_code == 200
    assert protegida.cliente.get("/estaticos/estilo.css").status_code == 200
    assert protegida.cliente.get("/entrar").status_code == 200


def test_sem_senha_onde_ela_e_exigida_o_site_sai_do_ar(engine_de_teste: Engine) -> None:
    """Na Vercel, esquecer a senha não pode deixar o clube aberto na internet."""
    aplicacao = criar_aplicacao(Contexto(engine_de_teste), exigir_senha=True)
    with TestClient(aplicacao) as cliente:
        pagina = cliente.get("/")
        api = cliente.get("/api/v1/clubes")

    assert pagina.status_code == 503
    assert "FILMES_E_CUBOS_SENHA" in pagina.text
    assert api.status_code == 503
    assert api.json()["codigo"] == "senha_nao_configurada"


def test_cookie_seguro_so_viaja_por_https(engine_de_teste: Engine) -> None:
    aplicacao = criar_aplicacao(Contexto(engine_de_teste), senha=SENHA, cookies_seguros=True)
    with TestClient(aplicacao, base_url="https://testserver") as cliente:
        resposta = cliente.post(
            "/entrar", data={"senha": SENHA, "proximo": "/"}, follow_redirects=False
        )

    cookie = resposta.headers["set-cookie"].lower()
    assert "secure" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_aviso_de_sucesso_aparece_uma_vez(web: WebDeTeste) -> None:
    pagina = web.agir("/clubes", nome="Filmes e Cubos")

    assert avisos(pagina) == ["Clube Filmes e Cubos criado."]
    assert avisos(web.abrir(str(web.cliente.get("/").url.path))) == []
