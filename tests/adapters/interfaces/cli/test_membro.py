"""Testes dos comandos de membro."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_cadastrar_membro_aparece_na_listagem(cli: CliDeTeste, clube_id: str) -> None:
    cli.executar_ok("membro", "cadastrar", "Iano", "--apelido", "Kuhl")

    saida = cli.executar_ok("membro", "listar").stdout
    assert "Iano" in saida
    assert "Kuhl" in saida
    assert "ativo" in saida


def test_membro_sem_apelido_mostra_marcador_de_campo_ausente(
    cli: CliDeTeste, membro_id: str
) -> None:
    linha = _linha_do_membro(cli.executar_ok("membro", "listar").stdout, "Iano")

    assert "—" in linha


def test_desativar_membro_mantem_ele_no_historico(cli: CliDeTeste, membro_id: str) -> None:
    cli.executar_ok("membro", "desativar", membro_id)

    linha = _linha_do_membro(cli.executar_ok("membro", "listar").stdout, "Iano")
    assert "inativo" in linha


def test_listar_apenas_ativos_omite_desativados(
    cli: CliDeTeste, membro_id: str, outro_membro_id: str
) -> None:
    cli.executar_ok("membro", "desativar", membro_id)

    saida = cli.executar_ok("membro", "listar", "--apenas-ativos").stdout
    assert "Iano" not in saida
    assert "Bia" in saida


def test_desativar_membro_inexistente_falha(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar("membro", "desativar", str(uuid4()))

    assert resultado.exit_code == 1
    assert "não encontrado" in resultado.stderr


def test_cadastrar_membro_sem_clube_cadastrado_orienta_o_usuario(cli: CliDeTeste) -> None:
    resultado = cli.executar("membro", "cadastrar", "Iano")

    assert resultado.exit_code == 1
    assert "clube criar" in resultado.stderr


def _linha_do_membro(saida: str, nome: str) -> str:
    return next(linha for linha in saida.splitlines() if nome in linha)


def test_reativar_membro_desativado(cli: CliDeTeste, membro_id: str) -> None:
    cli.executar_ok("membro", "desativar", membro_id)

    cli.executar_ok("membro", "reativar", membro_id)

    assert "Iano" in cli.executar_ok("membro", "listar", "--apenas-ativos").stdout
