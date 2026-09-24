"""Conversão dos campos de formulário (sempre texto) para os tipos do domínio.

Um `<input>` vazio chega como `""`, e números digitados por pessoas
usam vírgula decimal. Estas funções tratam os dois casos e recusam o
que não dá para interpretar com `FormularioInvalidoError`, que a web
exibe como aviso. Faixas e regras (nota dentro da escala, tamanho de
rodada positivo) continuam sendo validadas pelo domínio.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Final

from filmes_e_cubos.adapters.interfaces.web.mensagens import FormularioInvalidoError
from filmes_e_cubos.domain.value_objects.nota import Nota

VALOR_DORMINHOCO: Final = "dorminhoco"
"""Valor da opção "cochilou" no campo de nota do formulário de avaliação."""


def texto_opcional(texto: str) -> str | None:
    """Texto sem espaços nas pontas; vazio vira `None`."""
    limpo = texto.strip()
    return limpo or None


def inteiro_opcional(texto: str, *, campo: str) -> int | None:
    limpo = texto.strip()
    if not limpo:
        return None
    try:
        return int(limpo)
    except ValueError as erro:
        raise FormularioInvalidoError(f"{campo}: {texto!r} não é um número inteiro.") from erro


def decimal_opcional(texto: str, *, campo: str) -> Decimal | None:
    limpo = texto.strip()
    if not limpo:
        return None
    try:
        valor = Decimal(limpo.replace(",", "."))
    except InvalidOperation as erro:
        raise FormularioInvalidoError(f"{campo}: {texto!r} não é um número.") from erro
    if not valor.is_finite():
        raise FormularioInvalidoError(f"{campo}: {texto!r} não é um número.")
    return valor


def nota_ou_dorminhoco(texto: str) -> Nota | None:
    """A nota escolhida, ou `None` se a opção foi "cochilou" (dorminhoco).

    Campo vazio é recusado: como cada membro avalia uma vez só, não dá
    para deixar que um formulário incompleto registre um dorminhoco.
    """
    limpo = texto.strip()
    if limpo == VALOR_DORMINHOCO:
        return None
    valor = decimal_opcional(limpo, campo="Nota")
    if valor is None:
        raise FormularioInvalidoError("Escolha uma nota — ou marque que o membro cochilou.")
    return Nota.criar(valor)
