"""Testes dos comandos do Óscar do Filmes e Cubos."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from tests.adapters.interfaces.cli.conftest import CliDeTeste


@pytest.fixture
def temporada_id(cli: CliDeTeste, clube_id: str) -> str:
    return cli.criar("oscar", "temporada", "abrir")


@pytest.fixture
def categoria_id(cli: CliDeTeste, temporada_id: str) -> str:
    return cli.criar("oscar", "categoria", "definir", "Melhor veículo")


@pytest.fixture
def filme_assistido(cli: CliDeTeste, indicacao_id: str) -> str:
    """Um filme com sessão registrada no ano corrente — requisito para ser nomeado."""
    cli.executar_ok("sessao", "registrar", indicacao_id)
    linha = next(
        linha
        for linha in cli.executar_ok("filme", "listar").stdout.splitlines()
        if "Parasita" in linha
    )
    return linha.split()[0]


def test_temporada_usa_o_ano_corrente_por_padrao(cli: CliDeTeste, clube_id: str) -> None:
    cli.executar_ok("oscar", "temporada", "abrir")

    saida = cli.executar_ok("oscar", "temporada", "listar").stdout
    assert str(date.today().year) in saida
    assert "Filmes e Cubos" in saida


def test_temporada_aceita_ano_e_nome_explicitos(cli: CliDeTeste, clube_id: str) -> None:
    cli.executar_ok("oscar", "temporada", "abrir", "--ano", "2020", "--nome", "Óscar da Pandemia")

    saida = cli.executar_ok("oscar", "temporada", "listar").stdout
    assert "2020" in saida
    assert "Óscar da Pandemia" in saida


def test_categoria_e_variavel_por_padrao(cli: CliDeTeste, temporada_id: str) -> None:
    cli.executar_ok("oscar", "categoria", "definir", "Pior criança")

    linha = _linha(cli.executar_ok("oscar", "categoria", "listar").stdout, "Pior criança")
    assert "variavel" in linha


def test_categoria_pode_ser_fixa(cli: CliDeTeste, temporada_id: str) -> None:
    cli.executar_ok(
        "oscar", "categoria", "definir", "Melhor filme", "--tipo", "fixa", "--descricao", "O melhor"
    )

    linha = _linha(cli.executar_ok("oscar", "categoria", "listar").stdout, "Melhor filme")
    assert "fixa" in linha
    assert "O melhor" in linha


def test_tipo_de_categoria_invalido_e_recusado_pelo_parser(
    cli: CliDeTeste, temporada_id: str
) -> None:
    resultado = cli.executar("oscar", "categoria", "definir", "Categoria Torta", "--tipo", "outra")

    assert resultado.exit_code == 2  # erro de uso do próprio parser, não do domínio


def test_categoria_sem_temporada_do_ano_orienta_o_usuario(cli: CliDeTeste, clube_id: str) -> None:
    resultado = cli.executar("oscar", "categoria", "definir", "Melhor veículo")

    assert resultado.exit_code == 1
    assert "temporada do Óscar" in resultado.stderr


def test_nomear_filme_nao_assistido_e_recusado(
    cli: CliDeTeste, categoria_id: str, filme_id: str
) -> None:
    resultado = cli.executar(
        "oscar", "nomear", "--categoria-id", categoria_id, "--filme-id", filme_id
    )

    assert resultado.exit_code == 1
    assert "assistido" in resultado.stderr


def test_nomear_filme_assistido_no_ano_funciona(
    cli: CliDeTeste, categoria_id: str, filme_assistido: str
) -> None:
    resultado = cli.executar(
        "oscar", "nomear", "--categoria-id", categoria_id, "--filme-id", filme_assistido
    )

    assert resultado.exit_code == 0


def test_apurar_pergunta_a_vencedora_e_premia_quem_indicou(
    cli: CliDeTeste, categoria_id: str, filme_assistido: str
) -> None:
    _nomear(cli, categoria_id, filme_assistido)

    resultado = cli.executar_ok("oscar", "apurar", categoria_id, entrada="1\n")

    assert "Parasita" in resultado.stdout  # a nomeação foi listada para escolha
    assert "Troféu para Iano" in resultado.stdout
    categorias = cli.executar_ok("oscar", "categoria", "listar").stdout
    assert "Iano" in _linha(categorias, "Melhor veículo")


def test_apurar_reprompta_quando_a_escolha_esta_fora_da_faixa(
    cli: CliDeTeste, categoria_id: str, filme_assistido: str
) -> None:
    _nomear(cli, categoria_id, filme_assistido)

    resultado = cli.executar_ok("oscar", "apurar", categoria_id, entrada="9\n1\n")

    assert "Escolha um número entre 1 e 1." in resultado.stderr
    assert "Troféu para Iano" in resultado.stdout


def test_apurar_categoria_sem_nomeacoes_falha(cli: CliDeTeste, categoria_id: str) -> None:
    resultado = cli.executar("oscar", "apurar", categoria_id)

    assert resultado.exit_code == 1
    assert "nomeação" in resultado.stderr


def test_apurar_duas_vezes_falha(cli: CliDeTeste, categoria_id: str, filme_assistido: str) -> None:
    _nomear(cli, categoria_id, filme_assistido)
    cli.executar_ok("oscar", "apurar", categoria_id, entrada="1\n")

    resultado = cli.executar("oscar", "apurar", categoria_id, entrada="1\n")
    assert resultado.exit_code == 1
    assert "já foi apurada" in resultado.stderr


def test_vencedor_de_sessao_democracia_exige_membro_manual(
    cli: CliDeTeste, categoria_id: str, rodada_aberta: str, outro_filme_id: str, membro_id: str
) -> None:
    democracia = cli.criar("indicacao", "democracia", "--filme-id", outro_filme_id)
    cli.executar_ok("sessao", "registrar", democracia)
    _nomear(cli, categoria_id, outro_filme_id)

    sem_membro = cli.executar("oscar", "apurar", categoria_id, entrada="1\n")
    assert sem_membro.exit_code == 1
    assert "membro_vencedor_manual_id" in sem_membro.stderr

    com_membro = cli.executar_ok(
        "oscar", "apurar", categoria_id, "--membro-vencedor-id", membro_id, entrada="1\n"
    )
    assert "Troféu para Iano" in com_membro.stdout


def test_nomear_para_categoria_inexistente_falha(cli: CliDeTeste, filme_assistido: str) -> None:
    resultado = cli.executar(
        "oscar", "nomear", "--categoria-id", str(uuid4()), "--filme-id", filme_assistido
    )

    assert resultado.exit_code == 1
    assert "não encontrada" in resultado.stderr


def _nomear(cli: CliDeTeste, categoria_id: str, filme_id: str) -> None:
    cli.executar_ok("oscar", "nomear", "--categoria-id", categoria_id, "--filme-id", filme_id)


def _linha(saida: str, trecho: str) -> str:
    return next(linha for linha in saida.splitlines() if trecho in linha)


def test_marcar_e_remarcar_a_data_do_evento(cli: CliDeTeste, temporada_id: str) -> None:
    cli.executar_ok("oscar", "temporada", "data-evento", "2025-01-18")
    cli.executar_ok("oscar", "temporada", "data-evento", "25/01/2025")

    assert "2025-01-25" in cli.executar_ok("oscar", "temporada", "listar").stdout


def test_data_do_evento_invalida_e_recusada_pelo_parser(cli: CliDeTeste, temporada_id: str) -> None:
    resultado = cli.executar("oscar", "temporada", "data-evento", "18 de janeiro")

    assert resultado.exit_code == 2
