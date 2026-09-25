"""Testes dos comandos do catálogo de filmes."""

from __future__ import annotations

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_cadastrar_filme_com_todos_os_campos(cli: CliDeTeste) -> None:
    cli.executar_ok(
        "filme",
        "cadastrar",
        "Parasita",
        "--ano",
        "2019",
        "--diretor",
        "Bong Joon-ho",
        "--id-externo",
        "tt6751668",
    )

    saida = cli.executar_ok("filme", "listar").stdout
    assert "Parasita" in saida
    assert "2019" in saida
    assert "Bong Joon-ho" in saida


def test_cadastrar_filme_so_com_titulo(cli: CliDeTeste) -> None:
    cli.executar_ok("filme", "cadastrar", "Filme Sem Ficha")

    linha = next(
        linha
        for linha in cli.executar_ok("filme", "listar").stdout.splitlines()
        if "Filme Sem Ficha" in linha
    )
    assert linha.count("—") == 3


def test_catalogo_independe_de_clube(cli: CliDeTeste) -> None:
    """Um `Filme` não pertence a um clube, então cadastrar não exige clube."""
    resultado = cli.executar("filme", "cadastrar", "Parasita")

    assert resultado.exit_code == 0


def test_cadastrar_filme_sem_titulo_falha(cli: CliDeTeste) -> None:
    resultado = cli.executar("filme", "cadastrar", "   ")

    assert resultado.exit_code == 1


def test_listar_sem_filmes_avisa(cli: CliDeTeste) -> None:
    assert "Nenhum filme cadastrado." in cli.executar_ok("filme", "listar").stdout


def test_cadastrar_filme_com_duracao(cli: CliDeTeste) -> None:
    cli.executar_ok("filme", "cadastrar", "Parasita", "--duracao", "132")

    assert "132 min" in cli.executar_ok("filme", "listar").stdout


def test_definir_duracao_de_filme_ja_cadastrado(cli: CliDeTeste, filme_id: str) -> None:
    resultado = cli.executar_ok("filme", "duracao", filme_id, "132")

    assert "Parasita" in resultado.stdout
    assert "132 min" in cli.executar_ok("filme", "listar").stdout


def test_duracao_zero_e_recusada(cli: CliDeTeste, filme_id: str) -> None:
    resultado = cli.executar("filme", "duracao", filme_id, "0")

    assert resultado.exit_code == 1
    assert "positiva" in resultado.stderr
