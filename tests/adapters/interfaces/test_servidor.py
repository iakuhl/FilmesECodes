"""Testes do entry point `filmes-e-cubos-servidor` e da fábrica do app.

O uvicorn é substituído por um dublê: o que interessa aqui é o que o
comando entrega a ele (fábrica, endereço, banco), não subir um servidor
de verdade num teste.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from filmes_e_cubos.adapters.composicao import VARIAVEL_DE_AMBIENTE_BANCO
from filmes_e_cubos.adapters.interfaces import servidor


@pytest.fixture
def chamadas_ao_uvicorn(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    chamadas: list[dict[str, Any]] = []

    def run_falso(app: str, **opcoes: Any) -> None:
        chamadas.append({"app": app, **opcoes})

    monkeypatch.setattr(servidor.uvicorn, "run", run_falso)
    # O comando grava o caminho do banco no ambiente do processo. O `setenv`
    # registra o estado original para o monkeypatch restaurá-lo no fim do
    # teste; o `delenv` parte de um ambiente limpo.
    monkeypatch.setenv(VARIAVEL_DE_AMBIENTE_BANCO, "")
    monkeypatch.delenv(VARIAVEL_DE_AMBIENTE_BANCO)
    return chamadas


def test_padrao_escuta_so_nesta_maquina(chamadas_ao_uvicorn: list[dict[str, Any]]) -> None:
    resultado = CliRunner().invoke(servidor.comando, [])

    assert resultado.exit_code == 0, resultado.output
    (chamada,) = chamadas_ao_uvicorn
    assert chamada["app"] == f"{servidor.__name__}:criar_aplicacao_do_ambiente"
    assert chamada["factory"] is True
    assert chamada["host"] == "127.0.0.1"
    assert chamada["port"] == 8000
    assert chamada["reload"] is False


def test_opcoes_chegam_ao_uvicorn_e_o_banco_ao_ambiente(
    chamadas_ao_uvicorn: list[dict[str, Any]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    banco = tmp_path / "clube.db"

    resultado = CliRunner().invoke(
        servidor.comando,
        ["--host", "0.0.0.0", "--porta", "9000", "--db-path", str(banco), "--recarregar"],
    )

    assert resultado.exit_code == 0, resultado.output
    (chamada,) = chamadas_ao_uvicorn
    assert (chamada["host"], chamada["port"], chamada["reload"]) == ("0.0.0.0", 9000, True)
    assert servidor.os.environ[VARIAVEL_DE_AMBIENTE_BANCO] == str(banco)


def test_fabrica_do_ambiente_usa_o_banco_configurado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    banco = tmp_path / "do_ambiente.db"
    monkeypatch.setenv(VARIAVEL_DE_AMBIENTE_BANCO, str(banco))

    with TestClient(servidor.criar_aplicacao_do_ambiente()) as cliente:
        resposta = cliente.post("/api/v1/clubes", json={"nome": "Filmes e Cubos"})

    assert resposta.status_code == 201
    assert banco.exists()


def test_ajuda_do_comando(chamadas_ao_uvicorn: list[dict[str, Any]]) -> None:
    resultado = CliRunner().invoke(servidor.comando, ["--help"])

    assert resultado.exit_code == 0
    assert "--porta" in resultado.output
    assert chamadas_ao_uvicorn == []
