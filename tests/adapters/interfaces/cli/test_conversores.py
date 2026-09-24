"""Testes das conversões entre o texto da linha de comando e o domínio."""

from __future__ import annotations

from decimal import Decimal

import pytest

from filmes_e_cubos.adapters.interfaces.cli.conversores import (
    TipoCategoriaCli,
    converter_decimal,
    converter_nota,
)
from filmes_e_cubos.adapters.interfaces.cli.erros import CliError
from filmes_e_cubos.domain.exceptions.avaliacao import NotaInvalidaError
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


@pytest.mark.parametrize(("texto", "esperado"), [("4.5", "4.5"), ("4,5", "4.5"), ("5", "5")])
def test_decimal_aceita_ponto_e_virgula(texto: str, esperado: str) -> None:
    assert converter_decimal(texto, opcao="--nota") == Decimal(esperado)


def test_decimal_preserva_precisao_exata() -> None:
    """A conversão nunca passa por `float`, que arredondaria."""
    assert converter_decimal("0.1", opcao="--passo") == Decimal("0.1")


def test_decimal_invalido_vira_erro_de_cli_nomeando_a_opcao() -> None:
    with pytest.raises(CliError, match="--passo"):
        converter_decimal("muito", opcao="--passo")


def test_nota_ausente_significa_dorminhoco() -> None:
    assert converter_nota(None) is None


def test_nota_presente_vira_value_object() -> None:
    nota = converter_nota("4,5")

    assert nota is not None
    assert nota.valor == Decimal("4.5")


def test_nota_negativa_e_recusada_pelo_dominio() -> None:
    """A faixa válida é da `EscalaAvaliacao`; só o "ser positiva" é da `Nota`."""
    with pytest.raises(NotaInvalidaError):
        converter_nota("-1")


@pytest.mark.parametrize(
    ("cli", "dominio"),
    [
        (TipoCategoriaCli.FIXA, TipoCategoriaOscar.FIXA),
        (TipoCategoriaCli.VARIAVEL, TipoCategoriaOscar.VARIAVEL),
    ],
)
def test_tipo_de_categoria_mapeia_para_o_dominio(
    cli: TipoCategoriaCli, dominio: TipoCategoriaOscar
) -> None:
    assert cli.para_dominio() is dominio


def test_todo_tipo_de_categoria_do_dominio_tem_espelho_na_cli() -> None:
    """Se o domínio ganhar um tipo novo, este teste cobra o espelho da CLI."""
    espelhados = {tipo.para_dominio() for tipo in TipoCategoriaCli}

    assert espelhados == set(TipoCategoriaOscar)
