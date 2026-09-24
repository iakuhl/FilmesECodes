"""Testes do comando de registro de sessão."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_registrar_sessao_marca_a_indicacao_como_assistida(
    cli: CliDeTeste, indicacao_id: str
) -> None:
    cli.executar_ok("sessao", "registrar", indicacao_id)

    assert "assistida" in cli.executar_ok("rodada", "status").stdout


def test_sessao_pode_ser_registrada_sem_sorteio_previo(
    cli: CliDeTeste, indicacao_id: str
) -> None:
    """O sorteio é apoio opcional: uma indicação pendente pode ir direto para a sessão."""
    resultado = cli.executar("sessao", "registrar", indicacao_id)

    assert resultado.exit_code == 0


def test_sessao_tambem_funciona_depois_do_sorteio(cli: CliDeTeste, indicacao_id: str) -> None:
    cli.executar_ok("indicacao", "sortear")

    assert cli.executar("sessao", "registrar", indicacao_id).exit_code == 0


def test_sem_presentes_assume_todos_os_membros_ativos(
    cli: CliDeTeste, indicacao_id: str, outro_membro_id: str
) -> None:
    resultado = cli.executar_ok("sessao", "registrar", indicacao_id)

    assert "2 presente(s)" in resultado.stdout


def test_membro_desativado_nao_entra_na_presenca_padrao(
    cli: CliDeTeste, indicacao_id: str, outro_membro_id: str
) -> None:
    cli.executar_ok("membro", "desativar", outro_membro_id)

    assert "1 presente(s)" in cli.executar_ok("sessao", "registrar", indicacao_id).stdout


def test_presentes_explicitos_tem_precedencia(
    cli: CliDeTeste, indicacao_id: str, membro_id: str, outro_membro_id: str
) -> None:
    resultado = cli.executar_ok("sessao", "registrar", indicacao_id, "--presente", membro_id)

    assert "1 presente(s)" in resultado.stdout


def test_opcao_presente_e_repetivel(
    cli: CliDeTeste, indicacao_id: str, membro_id: str, outro_membro_id: str
) -> None:
    resultado = cli.executar_ok(
        "sessao",
        "registrar",
        indicacao_id,
        "--presente",
        membro_id,
        "--presente",
        outro_membro_id,
    )

    assert "2 presente(s)" in resultado.stdout


def test_registrar_duas_vezes_a_mesma_indicacao_falha(
    cli: CliDeTeste, indicacao_id: str
) -> None:
    cli.executar_ok("sessao", "registrar", indicacao_id)

    resultado = cli.executar("sessao", "registrar", indicacao_id)
    assert resultado.exit_code == 1


def test_indicacao_inexistente_falha(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar("sessao", "registrar", str(uuid4()))

    assert resultado.exit_code == 1
    assert "não encontrada" in resultado.stderr
