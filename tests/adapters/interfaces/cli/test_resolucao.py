"""Testes da resolução automática de clube, rodada e temporada.

A conveniência de omitir ids só se sustenta se a CLI for explícita quando
não consegue decidir sozinha — é isso que estes testes protegem.
"""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_clube_unico_e_assumido_sem_precisar_de_id(cli: CliDeTeste, clube_id: str) -> None:
    assert cli.executar("membro", "cadastrar", "Iano").exit_code == 0


def test_com_varios_clubes_a_cli_pede_para_escolher(cli: CliDeTeste, clube_id: str) -> None:
    cli.executar_ok("clube", "criar", "Cineclube do Bairro")

    resultado = cli.executar("membro", "cadastrar", "Iano")
    assert resultado.exit_code == 1
    assert "--clube-id" in resultado.stderr


def test_clube_id_explicito_desempata(cli: CliDeTeste, clube_id: str) -> None:
    outro = cli.criar("clube", "criar", "Cineclube do Bairro")

    cli.executar_ok("membro", "cadastrar", "Iano", "--clube-id", clube_id)
    cli.executar_ok("membro", "cadastrar", "Duda", "--clube-id", outro)

    assert "Duda" not in cli.executar_ok("membro", "listar", "--clube-id", clube_id).stdout
    assert "Iano" not in cli.executar_ok("membro", "listar", "--clube-id", outro).stdout


def test_clube_inexistente_por_id_falha(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar("membro", "cadastrar", "Iano", "--clube-id", str(uuid4()))

    assert resultado.exit_code == 1
    assert "não encontrado" in resultado.stderr


def test_sem_clube_algum_a_cli_ensina_o_proximo_passo(cli: CliDeTeste) -> None:
    resultado = cli.executar("membro", "listar")

    assert resultado.exit_code == 1
    assert "clube criar" in resultado.stderr


def test_rodada_aberta_e_assumida(cli: CliDeTeste, rodada_aberta: str, membro_id: str) -> None:
    filme = cli.criar("filme", "cadastrar", "Parasita")

    assert (
        cli.executar(
            "indicacao", "indicar", "--membro-id", membro_id, "--filme-id", filme
        ).exit_code
        == 0
    )


def test_rodada_id_explicito_permite_operar_rodada_nao_aberta(
    cli: CliDeTeste, indicacao_id: str
) -> None:
    rodada_id = next(
        linha.removeprefix("Id: ").strip()
        for linha in cli.executar_ok("rodada", "status").stdout.splitlines()
        if linha.startswith("Id: ")
    )
    cli.executar_ok("sessao", "registrar", indicacao_id)
    cli.executar_ok("rodada", "encerrar")

    assert cli.executar("rodada", "status", "--rodada-id", rodada_id).exit_code == 0


def test_temporada_do_ano_corrente_e_assumida(cli: CliDeTeste, clube_id: str) -> None:
    cli.executar_ok("oscar", "temporada", "abrir")

    assert cli.executar("oscar", "categoria", "definir", "Melhor veículo").exit_code == 0


def test_temporada_de_outro_ano_precisa_de_id_explicito(cli: CliDeTeste, clube_id: str) -> None:
    antiga = cli.criar("oscar", "temporada", "abrir", "--ano", "2020")

    sem_id = cli.executar("oscar", "categoria", "definir", "Melhor veículo")
    assert sem_id.exit_code == 1

    com_id = cli.executar(
        "oscar", "categoria", "definir", "Melhor veículo", "--temporada-id", antiga
    )
    assert com_id.exit_code == 0


def test_temporada_inexistente_por_id_falha(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar("oscar", "categoria", "listar", "--temporada-id", str(uuid4()))

    assert resultado.exit_code == 1
    assert "não encontrada" in resultado.stderr
