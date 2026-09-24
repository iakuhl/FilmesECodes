"""Fixtures dos testes da API HTTP.

Como os testes da CLI, estes exercitam a API de verdade: o app ASGI
completo (o mesmo que o servidor serve, com middleware e sub-app
montado), o composition root real e um SQLite real em arquivo
temporário. Nada é fake.

As fixtures encadeadas (`clube` -> `membro` -> `rodada` -> `indicacao`
-> `sessao`) montam o cenário sempre pela própria API: um teste que
preparasse o estado inserindo linhas no banco deixaria de perceber se a
rota de preparo quebrou.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.servidor import PREFIXO_DA_API, criar_aplicacao
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine

Json = dict[str, Any]


@dataclass(frozen=True)
class ApiDeTeste:
    """Faz requisições à API sob `/api/v1` e ajuda a conferir as respostas."""

    cliente: TestClient

    def get(self, caminho: str, **parametros: Any) -> Response:
        return self.cliente.get(PREFIXO_DA_API + caminho, params=parametros or None)

    def post(self, caminho: str, corpo: Any = None) -> Response:
        return self.cliente.post(PREFIXO_DA_API + caminho, json=corpo)

    def obter(self, caminho: str, **parametros: Any) -> Any:
        """GET esperando 200; devolve o corpo já decodificado."""
        resposta = self.get(caminho, **parametros)
        assert resposta.status_code == 200, resposta.text
        return resposta.json()

    def criar(self, caminho: str, corpo: Any = None) -> Json:
        """POST esperando 201; devolve o recurso criado."""
        resposta = self.post(caminho, corpo)
        assert resposta.status_code == 201, resposta.text
        corpo_da_resposta: Json = resposta.json()
        return corpo_da_resposta

    def executar(self, caminho: str, corpo: Any = None) -> Json:
        """POST de uma ação que devolve 200 (ex.: encerrar, desativar)."""
        resposta = self.post(caminho, corpo)
        assert resposta.status_code == 200, resposta.text
        corpo_da_resposta: Json = resposta.json()
        return corpo_da_resposta


def assert_problema(resposta: Response, status: int, codigo: str) -> Json:
    """Confere uma resposta de erro no formato `application/problem+json`."""
    assert resposta.status_code == status, resposta.text
    assert resposta.headers["content-type"] == "application/problem+json"
    corpo: Json = resposta.json()
    assert corpo["status"] == status
    assert corpo["codigo"] == codigo
    assert corpo["type"] == "about:blank"
    assert corpo["title"]
    assert corpo["detail"]
    return corpo


@pytest.fixture
def api(tmp_path: Path) -> Iterator[ApiDeTeste]:
    contexto = Contexto(criar_engine(tmp_path / "filmes_e_cubos_api.db"))
    with TestClient(criar_aplicacao(contexto)) as cliente:
        yield ApiDeTeste(cliente)


@pytest.fixture
def clube(api: ApiDeTeste) -> Json:
    return api.criar("/clubes", {"nome": "Filmes e Cubos"})


@pytest.fixture
def membro(api: ApiDeTeste, clube: Json) -> Json:
    return api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Iano", "apelido": "Ianinho"})


@pytest.fixture
def outro_membro(api: ApiDeTeste, clube: Json) -> Json:
    return api.criar(f"/clubes/{clube['id']}/membros", {"nome": "Bia"})


@pytest.fixture
def filme(api: ApiDeTeste) -> Json:
    return api.criar(
        "/filmes", {"titulo": "Parasita", "ano_lancamento": 2019, "diretor": "Bong Joon-ho"}
    )


@pytest.fixture
def outro_filme(api: ApiDeTeste) -> Json:
    return api.criar("/filmes", {"titulo": "Interestelar", "ano_lancamento": 2014})


@pytest.fixture
def rodada(api: ApiDeTeste, clube: Json) -> Json:
    return api.criar(f"/clubes/{clube['id']}/rodadas")


@pytest.fixture
def indicacao(api: ApiDeTeste, rodada: Json, membro: Json, filme: Json) -> Json:
    return api.criar(
        f"/rodadas/{rodada['id']}/indicacoes",
        {"membro_id": membro["id"], "filme_id": filme["id"]},
    )


@pytest.fixture
def sessao(api: ApiDeTeste, indicacao: Json) -> Json:
    return api.criar(f"/indicacoes/{indicacao['id']}/sessao")
