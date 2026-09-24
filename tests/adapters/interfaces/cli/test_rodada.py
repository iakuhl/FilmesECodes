"""Testes dos comandos de rodada."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_abrir_rodada_numera_a_partir_de_um(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar_ok("rodada", "abrir")

    assert "Rodada 1 aberta" in resultado.stdout


def test_nao_permite_duas_rodadas_abertas(cli: CliDeTeste, rodada_aberta: str) -> None:
    resultado = cli.executar("rodada", "abrir")

    assert resultado.exit_code == 1
    assert "já existe uma rodada aberta" in resultado.stderr.lower()


def test_status_mostra_a_rodada_aberta_e_suas_indicacoes(
    cli: CliDeTeste, indicacao_id: str
) -> None:
    saida = cli.executar_ok("rodada", "status").stdout

    assert "Rodada 1 — aberta" in saida
    assert "Parasita" in saida
    assert "Iano" in saida
    assert "normal" in saida
    assert "pendente" in saida


def test_status_de_rodada_sem_indicacoes_avisa(cli: CliDeTeste, rodada_aberta: str) -> None:
    saida = cli.executar_ok("rodada", "status").stdout

    assert "Nenhuma indicação nesta rodada ainda." in saida


def test_status_aceita_rodada_encerrada_por_id(cli: CliDeTeste, indicacao_id: str) -> None:
    cli.executar_ok("sessao", "registrar", indicacao_id)
    rodada_id = _id_da_rodada(cli)
    cli.executar_ok("rodada", "encerrar")

    saida = cli.executar_ok("rodada", "status", "--rodada-id", rodada_id).stdout
    assert "encerrada em" in saida
    assert "assistida" in saida


def test_encerrar_exige_todas_as_indicacoes_assistidas(cli: CliDeTeste, indicacao_id: str) -> None:
    resultado = cli.executar("rodada", "encerrar")

    assert resultado.exit_code == 1
    assert resultado.stderr.strip() != ""


def test_encerrar_libera_uma_nova_rodada(cli: CliDeTeste, indicacao_id: str) -> None:
    cli.executar_ok("sessao", "registrar", indicacao_id)
    cli.executar_ok("rodada", "encerrar")

    assert "Rodada 2 aberta" in cli.executar_ok("rodada", "abrir").stdout


def test_comandos_de_rodada_exigem_rodada_aberta(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar("rodada", "status")

    assert resultado.exit_code == 1
    assert "não tem rodada aberta" in resultado.stderr


def test_rodada_inexistente_por_id_falha(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar("rodada", "status", "--rodada-id", str(uuid4()))

    assert resultado.exit_code == 1
    assert "não encontrada" in resultado.stderr


def _id_da_rodada(cli: CliDeTeste) -> str:
    linha = next(
        linha
        for linha in cli.executar_ok("rodada", "status").stdout.splitlines()
        if linha.startswith("Id: ")
    )
    return linha.removeprefix("Id: ").strip()
