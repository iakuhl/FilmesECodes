"""Testes do value object Nota."""

from decimal import Decimal

import pytest

from filmes_e_cubos.domain.exceptions.avaliacao import NotaInvalidaError
from filmes_e_cubos.domain.value_objects.nota import Nota


def test_criar_nota_com_valor_positivo_e_valida() -> None:
    nota = Nota.criar("3.5")

    assert nota.valor == Decimal("3.5")


@pytest.mark.parametrize("valor_invalido", ["0", "-1", "-0.5"])
def test_criar_nota_nao_positiva_levanta_erro(valor_invalido: str) -> None:
    with pytest.raises(NotaInvalidaError):
        Nota.criar(valor_invalido)


def test_criar_nota_com_valor_nao_numerico_levanta_erro() -> None:
    with pytest.raises(NotaInvalidaError):
        Nota.criar("não é um número")
