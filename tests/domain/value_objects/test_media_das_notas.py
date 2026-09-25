"""Testes do value object MediaDasNotas."""

from decimal import Decimal
from fractions import Fraction

import pytest

from filmes_e_cubos.domain.value_objects.media_das_notas import MediaDasNotas
from filmes_e_cubos.domain.value_objects.nota import Nota


def test_sem_notas_nao_ha_media() -> None:
    assert MediaDasNotas.das_notas([]) is None


def test_guarda_a_soma_e_a_quantidade_das_notas() -> None:
    media = MediaDasNotas.das_notas([Nota.criar("4"), Nota.criar("3.5"), Nota.criar("3.5")])

    assert media == MediaDasNotas(soma=Decimal("11.0"), quantidade=3)


def test_valor_e_a_fracao_exata_sem_arredondamento() -> None:
    media = MediaDasNotas(soma=Decimal("11"), quantidade=3)

    assert media.valor == Fraction(11, 3)


def test_quantidade_precisa_ser_positiva() -> None:
    with pytest.raises(ValueError):
        MediaDasNotas(soma=Decimal("0"), quantidade=0)
