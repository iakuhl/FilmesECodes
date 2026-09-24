"""Value object que representa o valor numérico de uma nota."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from filmes_e_cubos.domain.exceptions.avaliacao import NotaInvalidaError


@dataclass(frozen=True, slots=True)
class Nota:
    """Um valor de nota positivo.

    Garante apenas que o valor é numericamente válido. A validação de
    faixa e granularidade (quais valores são aceitáveis) é responsabilidade
    de `EscalaAvaliacao`, para que a escala continue sendo uma configuração
    do clube e não uma regra fixa nesta classe.
    """

    valor: Decimal

    def __post_init__(self) -> None:
        if self.valor <= Decimal("0"):
            raise NotaInvalidaError(f"Nota deve ser positiva, recebido: {self.valor}")

    @classmethod
    def criar(cls, valor: Decimal | float | str) -> "Nota":
        try:
            valor_decimal = valor if isinstance(valor, Decimal) else Decimal(str(valor))
        except InvalidOperation as erro:
            raise NotaInvalidaError(f"Valor de nota inválido: {valor!r}") from erro
        return cls(valor_decimal)
