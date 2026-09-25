"""Testes da exibição da média em estrelas (decisão 19 de docs/PENDENCIAS.md)."""

from __future__ import annotations

from fractions import Fraction

import pytest

from filmes_e_cubos.adapters.interfaces.estrelas import media_em_estrelas


def test_exemplo_do_dono_do_produto() -> None:
    """3,66 -> * * * ⅔."""
    assert media_em_estrelas(Fraction(11, 3)) == "★★★⅔"


@pytest.mark.parametrize(
    ("media", "esperado"),
    [
        (Fraction(4), "★★★★"),
        (Fraction(9, 2), "★★★★½"),
        (Fraction(1, 2), "½"),
        (Fraction(13, 4), "★★★¼"),
        (Fraction(21, 5), "★★★★⅕"),
        (Fraction(47, 10), "★★★★⁷⁄₁₀"),
        (Fraction(23, 7), "★★★²⁄₇"),
        (Fraction(32, 9), "★★★⁵⁄₉"),
    ],
)
def test_estrelas_inteiras_mais_a_fracao_que_sobra(media: Fraction, esperado: str) -> None:
    assert media_em_estrelas(media) == esperado


def test_mais_de_dez_notas_usa_a_fracao_mais_proxima_ate_dez() -> None:
    assert media_em_estrelas(Fraction(34, 11)) == "★★★⅒"


def test_fracao_muito_pequena_some_e_muito_grande_vira_estrela() -> None:
    assert media_em_estrelas(Fraction(3) + Fraction(1, 50)) == "★★★"
    assert media_em_estrelas(Fraction(4) - Fraction(1, 50)) == "★★★★"
