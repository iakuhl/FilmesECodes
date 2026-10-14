"""Fixtures dos testes da web.

Como os da API, estes testes exercitam o app completo (o mesmo que o
servidor e a Vercel servem: web na raiz, API em `/api/v1`, sessão e
proteção por senha) contra um banco real. O cenário é montado pela própria
web, com formulários, e — para o que a web ainda não faz — pela API do
mesmo app; nunca inserindo linhas no banco.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import Engine

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.servidor import PREFIXO_DA_API, criar_aplicacao


@dataclass(frozen=True)
class WebDeTeste:
    """Navega pelo site como um navegador e ajuda a ler as páginas."""

    cliente: TestClient

    def abrir(self, caminho: str) -> BeautifulSoup:
        """GET de uma página que precisa abrir (200)."""
        resposta = self.cliente.get(caminho, follow_redirects=False)
        assert resposta.status_code == 200, (resposta.status_code, resposta.text[:500])
        return BeautifulSoup(resposta.text, "html.parser")

    def enviar(self, caminho: str, **campos: Any) -> Response:
        """POST de um formulário, sem seguir o redirecionamento."""
        return self.cliente.post(caminho, data=campos, follow_redirects=False)

    def agir(self, caminho: str, **campos: Any) -> BeautifulSoup:
        """Uma ação no padrão Post/Redirect/Get: confere o 303 e abre a página seguinte."""
        resposta = self.enviar(caminho, **campos)
        assert resposta.status_code == 303, (resposta.status_code, resposta.text[:500])
        return self.abrir(resposta.headers["location"])

    def api(self, metodo: str, caminho: str, corpo: Any = None) -> Any:
        """Chamada à API do mesmo app, para preparar o que a web ainda não faz."""
        resposta = self.cliente.request(metodo, PREFIXO_DA_API + caminho, json=corpo)
        assert resposta.status_code < 300, resposta.text
        return resposta.json()


def avisos(pagina: BeautifulSoup) -> list[str]:
    return [aviso.get_text(strip=True) for aviso in pagina.select(".aviso")]


def textos(pagina: BeautifulSoup, seletor: str) -> list[str]:
    return [elemento.get_text(" ", strip=True) for elemento in pagina.select(seletor)]


@pytest.fixture
def web(engine_de_teste: Engine) -> Iterator[WebDeTeste]:
    """O site sem senha — o uso local."""
    with TestClient(criar_aplicacao(Contexto(engine_de_teste))) as cliente:
        yield WebDeTeste(cliente)


@pytest.fixture
def clube_id(web: WebDeTeste) -> str:
    resposta = web.enviar("/clubes", nome="Filmes e Cubos", tamanho_rodada="3")
    assert resposta.status_code == 303
    web.abrir(resposta.headers["location"])  # como o navegador: consome o aviso de criação
    return str(resposta.headers["location"]).rsplit("/", 1)[-1]


def cadastrar_membro(web: WebDeTeste, clube_id: str, nome: str) -> str:
    """Cadastra pelo formulário e devolve o id (lido da API do mesmo app)."""
    web.agir(f"/clubes/{clube_id}/membros", nome=nome)
    return next(m["id"] for m in web.api("GET", f"/clubes/{clube_id}/membros") if m["nome"] == nome)


def cadastrar_filme(web: WebDeTeste, clube_id: str, titulo: str, **campos: str) -> str:
    web.agir(f"/clubes/{clube_id}/filmes", titulo=titulo, **campos)
    return next(f["id"] for f in web.api("GET", "/filmes") if f["titulo"] == titulo)
