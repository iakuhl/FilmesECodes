"""Value object que representa um endereço de e-mail."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from filmes_e_cubos.domain.exceptions.email import EnderecoDeEmailInvalidoError

_FORMA: Final = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@dataclass(frozen=True)
class EnderecoDeEmail:
    """Um endereço de e-mail, conferido só na forma (`alguem@dominio.tld`).

    Se a caixa existe, só o servidor de e-mail sabe; aqui basta recusar o
    que nem tem cara de endereço — um erro de digitação comum.
    """

    valor: str

    def __post_init__(self) -> None:
        limpo = self.valor.strip()
        if not _FORMA.fullmatch(limpo):
            raise EnderecoDeEmailInvalidoError(f"{self.valor!r} não é um endereço de e-mail.")
        object.__setattr__(self, "valor", limpo)

    def __str__(self) -> str:
        return self.valor
