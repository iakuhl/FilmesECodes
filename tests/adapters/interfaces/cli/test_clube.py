"""Testes dos comandos de clube."""

from __future__ import annotations

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_criar_clube_usa_a_configuracao_padrao_do_dominio(cli: CliDeTeste) -> None:
    cli.executar_ok("clube", "criar", "Filmes e Cubos")

    saida = cli.executar_ok("clube", "listar").stdout
    assert "Filmes e Cubos" in saida
    assert "5" in saida
    assert "0,5 a 5,0 (passo 0,5)" in saida


def test_criar_clube_aceita_configuracao_customizada(cli: CliDeTeste) -> None:
    cli.executar_ok(
        "clube",
        "criar",
        "Cineclube do Bairro",
        "--tamanho-rodada",
        "3",
        "--nota-minima",
        "1",
        "--nota-maxima",
        "10",
        "--passo",
        "1",
    )

    saida = cli.executar_ok("clube", "listar").stdout
    assert "Cineclube do Bairro" in saida
    assert "1 a 10 (passo 1)" in saida


def test_criar_clube_aceita_nota_com_virgula(cli: CliDeTeste) -> None:
    cli.executar_ok("clube", "criar", "Clube da Vírgula", "--nota-minima", "0,5")

    assert "0,5 a 5,0" in cli.executar_ok("clube", "listar").stdout


def test_criar_clube_recusa_valor_nao_numerico(cli: CliDeTeste) -> None:
    resultado = cli.executar("clube", "criar", "Clube Torto", "--nota-maxima", "muito")

    assert resultado.exit_code == 1
    assert "--nota-maxima" in resultado.stderr


def test_criar_clube_recusa_tamanho_de_rodada_invalido(cli: CliDeTeste) -> None:
    resultado = cli.executar("clube", "criar", "Clube Vazio", "--tamanho-rodada", "0")

    assert resultado.exit_code == 1
    assert "positivo" in resultado.stderr


def test_listar_sem_clubes_avisa_em_vez_de_imprimir_tabela_vazia(cli: CliDeTeste) -> None:
    saida = cli.executar_ok("clube", "listar").stdout

    assert "Nenhum clube cadastrado." in saida
    assert "ID" not in saida
