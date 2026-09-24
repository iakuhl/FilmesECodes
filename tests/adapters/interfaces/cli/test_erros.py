"""Testes do contrato de erro e do ponto de entrada da CLI.

O contrato que os comandos assumem (e que `erros.py` concentra) é: erro
esperado vai para `stderr` com código 1, e `stdout` fica limpo — para
que a saída de um comando continue podendo ser encadeada em um pipe.
"""

from __future__ import annotations

from pathlib import Path

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_erro_de_dominio_vira_codigo_1_com_mensagem_em_stderr(
    cli: CliDeTeste, rodada_aberta: str
) -> None:
    resultado = cli.executar("rodada", "abrir")

    assert resultado.exit_code == 1
    assert resultado.stderr.startswith("Erro: ")
    assert resultado.stdout == ""


def test_erro_de_uso_da_cli_segue_o_mesmo_contrato(cli: CliDeTeste) -> None:
    resultado = cli.executar("rodada", "abrir")  # nenhum clube cadastrado

    assert resultado.exit_code == 1
    assert resultado.stderr.startswith("Erro: ")
    assert resultado.stdout == ""


def test_erro_em_sub_app_aninhado_tambem_e_tratado(cli: CliDeTeste, clube_id: str) -> None:
    """`oscar categoria` é um sub-app dentro de outro sub-app."""
    resultado = cli.executar("oscar", "categoria", "listar")

    assert resultado.exit_code == 1
    assert resultado.stderr.startswith("Erro: ")


def test_argumento_malformado_e_erro_de_uso_do_parser(cli: CliDeTeste, clube_id: str) -> None:
    """Um id que não é UUID nem chega aos comandos: o Typer recusa antes."""
    resultado = cli.executar("membro", "desativar", "isso-nao-e-um-uuid")

    assert resultado.exit_code == 2


def test_ajuda_nao_cria_o_banco_de_dados(cli: CliDeTeste) -> None:
    """Consultar a ajuda não pode ter efeito colateral no diretório do usuário."""
    assert cli.executar("--help").exit_code == 0
    assert cli.executar("clube", "--help").exit_code == 0
    assert cli.executar("oscar", "categoria", "--help").exit_code == 0

    assert not cli.caminho_banco.exists()


def test_comando_real_cria_o_banco_no_caminho_pedido(cli: CliDeTeste) -> None:
    cli.executar_ok("clube", "listar")

    assert cli.caminho_banco.exists()


def test_banco_pode_vir_da_variavel_de_ambiente(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from filmes_e_cubos.adapters.interfaces.cli.main import app

    caminho = tmp_path / "por_ambiente.db"
    runner = CliRunner(env={"FILMES_E_CUBOS_DB": str(caminho)})

    assert runner.invoke(app, ["clube", "listar"]).exit_code == 0
    assert caminho.exists()


def test_sem_argumentos_a_cli_mostra_a_ajuda(cli: CliDeTeste) -> None:
    resultado = cli.executar()

    assert "Usage" in resultado.output
