"""Value object que representa a média das notas de uma sessão, como fração exata."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from filmes_e_cubos.domain.value_objects.nota import Nota


@dataclass(frozen=True, slots=True)
class MediaDasNotas:
    """A média das notas de uma sessão, guardada como soma e quantidade de notas.

    Guardar a fração (soma ÷ quantidade), e não o valor já dividido,
    preserva a média exata: 11 ÷ 3 continua sendo 11/3, sem virar 3,67
    nem 3,6666... (decisão 19 de docs/PENDENCIAS.md). Dorminhocos não têm
    nota e por isso não entram na conta. Como exibir a média (em
    estrelas) é assunto das interfaces.
    """

    soma: Decimal
    quantidade: int

    def __post_init__(self) -> None:
        # Só o próprio sistema cria médias, a partir de notas já validadas:
        # uma quantidade não positiva é defeito de programação, não uma
        # recusa de regra de negócio — por isso não é um `DomainError`.
        if self.quantidade < 1:
            raise ValueError(f"Uma média precisa de ao menos uma nota, recebido: {self.quantidade}")

    @classmethod
    def das_notas(cls, notas: Iterable[Nota]) -> MediaDasNotas | None:
        """A média das notas dadas, ou `None` se não houver nenhuma."""
        valores = [nota.valor for nota in notas]
        if not valores:
            return None
        return cls(soma=sum(valores, Decimal(0)), quantidade=len(valores))

    @property
    def valor(self) -> Fraction:
        """O valor exato da média."""
        return Fraction(self.soma) / self.quantidade
