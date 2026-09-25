"""A média das notas em estrelas, como todas as interfaces a exibem.

O dono do produto decidiu (decisão 19 de docs/PENDENCIAS.md) que a média
aparece como uma estrela por inteiro, seguida da fração que sobra, com
denominador de 2 a 10: 3,66... vira `★★★⅔`. A regra mora aqui, e não em
cada interface, para que a CLI, a API e a web mostrem sempre o mesmo.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Final

ESTRELA: Final = "★"

MAIOR_DENOMINADOR: Final = 10
"""Frações com denominador maior são aproximadas pela mais próxima até 10."""

_FRACOES_PRONTAS: Final[dict[Fraction, str]] = {
    Fraction(1, 2): "½",
    Fraction(1, 3): "⅓",
    Fraction(2, 3): "⅔",
    Fraction(1, 4): "¼",
    Fraction(3, 4): "¾",
    Fraction(1, 5): "⅕",
    Fraction(2, 5): "⅖",
    Fraction(3, 5): "⅗",
    Fraction(4, 5): "⅘",
    Fraction(1, 6): "⅙",
    Fraction(5, 6): "⅚",
    Fraction(1, 7): "⅐",
    Fraction(1, 8): "⅛",
    Fraction(3, 8): "⅜",
    Fraction(5, 8): "⅝",
    Fraction(7, 8): "⅞",
    Fraction(1, 9): "⅑",
    Fraction(1, 10): "⅒",
}
"""As frações que o Unicode tem como um caractere só."""

_SOBRESCRITOS: Final = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_SUBSCRITOS: Final = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_BARRA_DE_FRACAO: Final = "\u2044"


def media_em_estrelas(media: Fraction) -> str:
    """`Fraction(11, 3)` -> `"★★★⅔"`; `Fraction(4)` -> `"★★★★"`.

    A fração que sobra depois das estrelas inteiras é a mais próxima com
    denominador até 10 — exata sempre que a sessão teve até 10 notas. Se
    ela arredondar para zero ou para um inteiro, só aparecem estrelas.
    """
    inteiras = math.floor(media)
    resto = (media - inteiras).limit_denominator(MAIOR_DENOMINADOR)
    if resto == 1:
        inteiras, resto = inteiras + 1, Fraction(0)
    return ESTRELA * inteiras + (_fracao_em_texto(resto) if resto else "")


def _fracao_em_texto(fracao: Fraction) -> str:
    """O caractere pronto da fração, ou numerador e denominador compostos: `²⁄₇`."""
    pronta = _FRACOES_PRONTAS.get(fracao)
    if pronta is not None:
        return pronta
    numerador = str(fracao.numerator).translate(_SOBRESCRITOS)
    denominador = str(fracao.denominator).translate(_SUBSCRITOS)
    return f"{numerador}{_BARRA_DE_FRACAO}{denominador}"
