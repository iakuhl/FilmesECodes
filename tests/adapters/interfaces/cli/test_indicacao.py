"""Testes dos comandos de indicação e sorteio."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_indicar_usa_a_rodada_aberta_quando_nao_informada(
    cli: CliDeTeste, rodada_aberta: str, membro_id: str, filme_id: str
) -> None:
    cli.executar_ok("indicacao", "indicar", "--membro-id", membro_id, "--filme-id", filme_id)

    assert "Parasita" in cli.executar_ok("rodada", "status").stdout


def test_membro_nao_pode_indicar_duas_vezes_na_mesma_rodada(
    cli: CliDeTeste, indicacao_id: str, membro_id: str, outro_filme_id: str
) -> None:
    resultado = cli.executar(
        "indicacao", "indicar", "--membro-id", membro_id, "--filme-id", outro_filme_id
    )

    assert resultado.exit_code == 1
    assert "já indicou" in resultado.stderr


def test_membro_inativo_nao_indica(
    cli: CliDeTeste, rodada_aberta: str, membro_id: str, filme_id: str
) -> None:
    cli.executar_ok("membro", "desativar", membro_id)

    resultado = cli.executar(
        "indicacao", "indicar", "--membro-id", membro_id, "--filme-id", filme_id
    )
    assert resultado.exit_code == 1
    assert "inativo" in resultado.stderr


def test_indicar_filme_inexistente_falha(
    cli: CliDeTeste, rodada_aberta: str, membro_id: str
) -> None:
    resultado = cli.executar(
        "indicacao", "indicar", "--membro-id", membro_id, "--filme-id", str(uuid4())
    )

    assert resultado.exit_code == 1
    assert "não encontrado" in resultado.stderr


def test_democracia_entra_sem_membro_indicador(
    cli: CliDeTeste, rodada_aberta: str, filme_id: str
) -> None:
    cli.executar_ok("indicacao", "democracia", "--filme-id", filme_id)

    linha = next(
        linha
        for linha in cli.executar_ok("rodada", "status").stdout.splitlines()
        if "Parasita" in linha
    )
    assert "democracia" in linha
    assert "—" in linha


def test_democracia_nao_conta_na_cota_da_rodada(
    cli: CliDeTeste, clube_id: str, membro_id: str, filme_id: str, outro_filme_id: str
) -> None:
    cli.executar_ok("clube", "criar", "Clube de Um")  # não interfere: usamos --clube-id
    cli.executar_ok("rodada", "abrir", "--clube-id", clube_id)
    cli.executar_ok("indicacao", "democracia", "--filme-id", filme_id, "--clube-id", clube_id)

    resultado = cli.executar(
        "indicacao",
        "indicar",
        "--membro-id",
        membro_id,
        "--filme-id",
        outro_filme_id,
        "--clube-id",
        clube_id,
    )
    assert resultado.exit_code == 0


def test_sortear_marca_a_indicacao_como_sorteada(cli: CliDeTeste, indicacao_id: str) -> None:
    resultado = cli.executar_ok("indicacao", "sortear")

    assert "Parasita" in resultado.stdout
    assert "sorteada" in cli.executar_ok("rodada", "status").stdout


def test_sortear_sem_indicacao_pendente_falha(cli: CliDeTeste, indicacao_id: str) -> None:
    cli.executar_ok("indicacao", "sortear")

    resultado = cli.executar("indicacao", "sortear")
    assert resultado.exit_code == 1
    assert resultado.stderr.strip() != ""


def test_filme_ja_indicado_no_clube_e_recusado(
    cli: CliDeTeste, indicacao_id: str, outro_membro_id: str, filme_id: str
) -> None:
    resultado = cli.executar(
        "indicacao", "indicar", "--membro-id", outro_membro_id, "--filme-id", filme_id
    )

    assert resultado.exit_code == 1
    assert "já está indicado" in resultado.stderr
