"""Testes dos comandos da votação do Óscar: `oscar votacao`, `votar` e `confirmar`."""

from __future__ import annotations

import pytest

from tests.adapters.interfaces.cli.conftest import CliDeTeste


@pytest.fixture
def categoria_em_votacao(
    cli: CliDeTeste, indicacao_id: str, filme_id: str, outro_membro_id: str
) -> str:
    """Uma edição em votação, com Iano e Bia como eleitores e uma categoria de duas
    nomeações — o mesmo filme duas vezes, o que a decisão 20 permite.
    """
    cli.executar_ok("sessao", "registrar", indicacao_id)
    cli.executar_ok("oscar", "temporada", "abrir", "--nomeacoes-por-categoria", "2")
    categoria = cli.criar("oscar", "categoria", "definir", "Melhor veículo")
    cli.executar_ok("oscar", "temporada", "avancar")
    for _ in range(2):
        cli.executar_ok("oscar", "nomear", "--categoria-id", categoria, "--filme-id", filme_id)
    cli.executar_ok("oscar", "temporada", "avancar")
    return categoria


def _votar(cli: CliDeTeste, membro_id: str, categoria_id: str, *escolhas: str) -> None:
    cli.executar_ok(
        "oscar", "votar", "--membro-id", membro_id, "--categoria-id", categoria_id, *escolhas
    )


def test_votacao_mostra_as_candidatas_numeradas_e_o_andamento(
    cli: CliDeTeste, categoria_em_votacao: str
) -> None:
    saida = cli.executar_ok("oscar", "votacao").stdout

    assert "1º turno da votação" in saida
    assert "Melhor veículo" in saida
    assert "vote na 1ª e na 2ª opção" in saida
    assert saida.count("Parasita") == 2
    assert "votou em 0 de 1" in saida


def test_votar_pela_posicao_e_confirmar(
    cli: CliDeTeste, categoria_em_votacao: str, membro_id: str
) -> None:
    _votar(cli, membro_id, categoria_em_votacao, "2", "1")

    assert "votou em 1 de 1" in cli.executar_ok("oscar", "votacao").stdout
    confirmacao = cli.executar_ok("oscar", "confirmar", "--membro-id", membro_id).stdout
    assert "Cédula confirmada" in confirmacao
    assert "Ainda faltam confirmar: Bia" in confirmacao
    assert "confirmada" in _linha_do_eleitor(cli.executar_ok("oscar", "votacao").stdout, "Iano")


def test_voto_nao_muda_depois_da_confirmacao(
    cli: CliDeTeste, categoria_em_votacao: str, membro_id: str
) -> None:
    _votar(cli, membro_id, categoria_em_votacao, "1", "2")
    cli.executar_ok("oscar", "confirmar", "--membro-id", membro_id)

    resultado = cli.executar(
        "oscar", "votar", "--membro-id", membro_id, "--categoria-id", categoria_em_votacao, "2", "1"
    )

    assert resultado.exit_code == 1
    assert "já foi confirmada" in resultado.stderr


def test_ultima_confirmacao_termina_a_votacao(
    cli: CliDeTeste, categoria_em_votacao: str, membro_id: str, outro_membro_id: str
) -> None:
    for eleitor in (membro_id, outro_membro_id):
        _votar(cli, eleitor, categoria_em_votacao, "1", "2")
    cli.executar_ok("oscar", "confirmar", "--membro-id", membro_id)

    ultima = cli.executar_ok("oscar", "confirmar", "--membro-id", outro_membro_id).stdout

    assert "a votação terminou" in ultima
    assert "o placar já pode ser enviado" in cli.executar_ok("oscar", "votacao").stdout


def test_empate_abre_o_turno_seguinte(
    cli: CliDeTeste, categoria_em_votacao: str, membro_id: str, outro_membro_id: str
) -> None:
    _votar(cli, membro_id, categoria_em_votacao, "1", "2")
    _votar(cli, outro_membro_id, categoria_em_votacao, "2", "1")
    cli.executar_ok("oscar", "confirmar", "--membro-id", membro_id)

    ultima = cli.executar_ok("oscar", "confirmar", "--membro-id", outro_membro_id).stdout

    assert "começou o 2º turno" in ultima
    situacao = cli.executar_ok("oscar", "votacao").stdout
    assert "2º turno da votação" in situacao
    assert "ordene todas as candidatas" in situacao


def test_membro_cadastrado_durante_a_votacao_nao_vota(
    cli: CliDeTeste, categoria_em_votacao: str
) -> None:
    """Decisão 23: os eleitores ficam definidos quando a votação começa."""
    caio = cli.criar("membro", "cadastrar", "Caio")

    resultado = cli.executar(
        "oscar", "votar", "--membro-id", caio, "--categoria-id", categoria_em_votacao, "1", "2"
    )

    assert resultado.exit_code == 1
    assert "eleitores" in resultado.stderr
    assert "Caio" not in cli.executar_ok("oscar", "votacao").stdout


def test_membro_desativado_durante_a_votacao_continua_votando(
    cli: CliDeTeste, categoria_em_votacao: str, outro_membro_id: str
) -> None:
    """Decisão 23: desativar não tira ninguém da votação."""
    cli.executar_ok("membro", "desativar", outro_membro_id)

    _votar(cli, outro_membro_id, categoria_em_votacao, "1", "2")

    assert "Bia" in cli.executar_ok("oscar", "votacao").stdout


def test_posicao_inexistente_e_recusada(
    cli: CliDeTeste, categoria_em_votacao: str, membro_id: str
) -> None:
    resultado = cli.executar(
        "oscar", "votar", "--membro-id", membro_id, "--categoria-id", categoria_em_votacao, "7", "1"
    )

    assert resultado.exit_code == 1
    assert "posição 7" in resultado.stderr


def test_confirmar_sem_votar_lista_o_que_falta(
    cli: CliDeTeste, categoria_em_votacao: str, membro_id: str
) -> None:
    resultado = cli.executar("oscar", "confirmar", "--membro-id", membro_id)

    assert resultado.exit_code == 1
    assert "Falta votar em: Melhor veículo" in resultado.stderr


def test_votacao_antes_da_fase_de_votacao(cli: CliDeTeste, clube_id: str) -> None:
    cli.executar_ok("oscar", "temporada", "abrir")

    resultado = cli.executar("oscar", "votacao")

    assert resultado.exit_code == 1
    assert "ainda não chegou à votação" in resultado.stderr


def _linha_do_eleitor(saida: str, nome: str) -> str:
    return next(linha for linha in saida.splitlines() if linha.startswith(nome))
