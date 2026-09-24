"""Testes da formatação de saída da CLI."""

from __future__ import annotations

from decimal import Decimal

import pytest

from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    AUSENTE,
    echo_tabela,
    formatar_decimal,
    formatar_opcional,
)


def test_campo_ausente_vira_marcador() -> None:
    assert formatar_opcional(None) == AUSENTE


@pytest.mark.parametrize("valor", [0, "", False])
def test_valor_falsy_mas_presente_nao_vira_marcador(valor: object) -> None:
    assert formatar_opcional(valor) == str(valor)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(Decimal("4.5"), "4,5"), (Decimal("5.0"), "5,0"), (Decimal("1"), "1")],
)
def test_decimal_sai_com_virgula(valor: Decimal, esperado: str) -> None:
    assert formatar_decimal(valor) == esperado


def test_tabela_alinha_colunas_pela_celula_mais_larga(
    capsys: pytest.CaptureFixture[str],
) -> None:
    echo_tabela(("ID", "NOME"), [("1", "Iano"), ("2", "Bia")])

    linhas = capsys.readouterr().out.splitlines()
    assert linhas[0] == "ID  NOME"
    assert linhas[1] == "--  ----"
    assert linhas[2].startswith("1   Iano")
    assert linhas[3].startswith("2   Bia")


def test_tabela_respeita_cabecalho_mais_largo_que_os_dados(
    capsys: pytest.CaptureFixture[str],
) -> None:
    echo_tabela(("IDENTIFICADOR",), [("1",)])

    linhas = capsys.readouterr().out.splitlines()
    assert linhas[0] == "IDENTIFICADOR"
    assert linhas[2].startswith("1            ")


def test_tabela_sem_linhas_avisa_em_vez_de_imprimir_cabecalho(
    capsys: pytest.CaptureFixture[str],
) -> None:
    echo_tabela(("ID", "NOME"), [], vazio="Nada por aqui.")

    saida = capsys.readouterr().out
    assert saida.strip() == "Nada por aqui."
