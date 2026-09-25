"""Testes dos comandos de avaliação."""

from __future__ import annotations

from uuid import uuid4

from typer.testing import Result

from tests.adapters.interfaces.cli.conftest import CliDeTeste


def test_registrar_nota_aparece_na_listagem(
    cli: CliDeTeste, sessao_id: str, membro_id: str
) -> None:
    _avaliar(cli, sessao_id, membro_id, "--nota", "4.5")

    saida = cli.executar_ok("avaliacao", "listar", sessao_id).stdout
    assert "Iano" in saida
    assert "4,5" in saida


def test_nota_aceita_virgula_decimal(cli: CliDeTeste, sessao_id: str, membro_id: str) -> None:
    _avaliar(cli, sessao_id, membro_id, "--nota", "3,5")

    assert "3,5" in cli.executar_ok("avaliacao", "listar", sessao_id).stdout


def test_sem_nota_registra_dorminhoco(cli: CliDeTeste, sessao_id: str, membro_id: str) -> None:
    resultado = _avaliar(cli, sessao_id, membro_id)

    assert "dorminhoco" in resultado.stdout
    assert "dorminhoco" in cli.executar_ok("avaliacao", "listar", sessao_id).stdout


def test_comentario_e_exibido(cli: CliDeTeste, sessao_id: str, membro_id: str) -> None:
    _avaliar(cli, sessao_id, membro_id, "--nota", "5", "--comentario", "Obra-prima")

    assert "Obra-prima" in cli.executar_ok("avaliacao", "listar", sessao_id).stdout


def test_nota_fora_da_escala_do_clube_e_recusada(
    cli: CliDeTeste, sessao_id: str, membro_id: str
) -> None:
    resultado = _avaliar(cli, sessao_id, membro_id, "--nota", "7", esperado=1)

    assert "fora da escala" in resultado.stderr


def test_nota_fora_do_passo_da_escala_e_recusada(
    cli: CliDeTeste, sessao_id: str, membro_id: str
) -> None:
    resultado = _avaliar(cli, sessao_id, membro_id, "--nota", "4.3", esperado=1)

    assert "passo" in resultado.stderr


def test_nota_nao_numerica_e_recusada(cli: CliDeTeste, sessao_id: str, membro_id: str) -> None:
    resultado = _avaliar(cli, sessao_id, membro_id, "--nota", "bom", esperado=1)

    assert "--nota" in resultado.stderr


def test_membro_avalia_uma_sessao_uma_vez_so(
    cli: CliDeTeste, sessao_id: str, membro_id: str
) -> None:
    _avaliar(cli, sessao_id, membro_id, "--nota", "5")

    resultado = _avaliar(cli, sessao_id, membro_id, "--nota", "4", esperado=1)
    assert "já avaliou" in resultado.stderr


def test_avaliar_sessao_inexistente_falha(cli: CliDeTeste, membro_id: str) -> None:
    resultado = _avaliar(cli, str(uuid4()), membro_id, esperado=1)

    assert "não encontrada" in resultado.stderr


def test_listar_sessao_sem_avaliacoes_avisa(cli: CliDeTeste, sessao_id: str) -> None:
    saida = cli.executar_ok("avaliacao", "listar", sessao_id).stdout

    assert "Nenhuma avaliação registrada" in saida


def _avaliar(
    cli: CliDeTeste, sessao_id: str, membro_id: str, *extras: str, esperado: int = 0
) -> Result:
    resultado = cli.executar(
        "avaliacao", "registrar", "--sessao-id", sessao_id, "--membro-id", membro_id, *extras
    )
    assert resultado.exit_code == esperado, resultado.output
    return resultado


def test_quem_nao_esteve_na_sessao_nao_avalia(
    cli: CliDeTeste, sessao_id: str, membro_id: str
) -> None:
    chegou_depois = cli.criar("membro", "cadastrar", "Caio")

    resultado = _avaliar(cli, sessao_id, chegou_depois, "--nota", "4", esperado=1)

    assert "não esteve presente" in resultado.stderr


def test_media_da_sessao_aparece_em_estrelas(
    cli: CliDeTeste, indicacao_id: str, membro_id: str, outro_membro_id: str
) -> None:
    sessao_id = cli.criar("sessao", "registrar", indicacao_id)
    terceiro = cli.criar("membro", "cadastrar", "Caio")
    cli.executar_ok(
        "avaliacao", "registrar", "--sessao-id", sessao_id, "--membro-id", membro_id,
        "--nota", "4",
    )  # fmt: skip
    _avaliar(cli, sessao_id, outro_membro_id, "--nota", "3,5")

    listagem = cli.executar_ok("avaliacao", "listar", sessao_id).stdout

    assert "Média da sessão: ★★★¾ (2 notas)" in listagem
    assert _avaliar(cli, sessao_id, terceiro, esperado=1)
