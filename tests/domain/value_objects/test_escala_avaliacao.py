"""Testes do value object EscalaAvaliacao."""

from decimal import Decimal

import pytest

from filmes_e_cubos.domain.exceptions.avaliacao import (
    EscalaAvaliacaoInvalidaError,
    NotaForaDaEscalaError,
)
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.nota import Nota


def test_escala_padrao_e_meio_a_cinco_em_passos_de_meio() -> None:
    escala = EscalaAvaliacao.padrao()

    assert escala.nota_minima == Decimal("0.5")
    assert escala.nota_maxima == Decimal("5.0")
    assert escala.passo == Decimal("0.5")


@pytest.mark.parametrize("valor", ["0.5", "1.0", "3.5", "5.0"])
def test_validar_aceita_notas_dentro_da_escala_padrao(valor: str) -> None:
    escala = EscalaAvaliacao.padrao()

    escala.validar(Nota.criar(valor))  # não deve levantar


@pytest.mark.parametrize("valor", ["0.2", "5.5", "3.25"])
def test_validar_rejeita_notas_fora_da_escala_padrao(valor: str) -> None:
    escala = EscalaAvaliacao.padrao()

    with pytest.raises(NotaForaDaEscalaError):
        escala.validar(Nota.criar(valor))


def test_escala_com_passo_nao_positivo_levanta_erro() -> None:
    with pytest.raises(EscalaAvaliacaoInvalidaError):
        EscalaAvaliacao(nota_minima=Decimal("1"), nota_maxima=Decimal("5"), passo=Decimal("0"))


def test_escala_com_maxima_menor_que_minima_levanta_erro() -> None:
    with pytest.raises(EscalaAvaliacaoInvalidaError):
        EscalaAvaliacao(nota_minima=Decimal("5"), nota_maxima=Decimal("1"), passo=Decimal("0.5"))


def test_escala_com_intervalo_nao_multiplo_do_passo_levanta_erro() -> None:
    with pytest.raises(EscalaAvaliacaoInvalidaError):
        EscalaAvaliacao(nota_minima=Decimal("1"), nota_maxima=Decimal("5.2"), passo=Decimal("0.5"))
