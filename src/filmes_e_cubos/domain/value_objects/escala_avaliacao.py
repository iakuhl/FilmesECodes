"""Value object que representa a escala de notas aceita por um clube."""

from dataclasses import dataclass
from decimal import Decimal

from filmes_e_cubos.domain.exceptions.avaliacao import (
    EscalaAvaliacaoInvalidaError,
    NotaForaDaEscalaError,
)
from filmes_e_cubos.domain.value_objects.nota import Nota


@dataclass(frozen=True, slots=True)
class EscalaAvaliacao:
    """Faixa e granularidade de notas aceitas em avaliações de um clube."""

    nota_minima: Decimal
    nota_maxima: Decimal
    passo: Decimal

    def __post_init__(self) -> None:
        if self.passo <= Decimal("0"):
            raise EscalaAvaliacaoInvalidaError("O passo da escala deve ser positivo.")
        if self.nota_minima <= Decimal("0"):
            raise EscalaAvaliacaoInvalidaError("A nota mínima deve ser positiva.")
        if self.nota_maxima < self.nota_minima:
            raise EscalaAvaliacaoInvalidaError(
                "A nota máxima não pode ser menor que a nota mínima."
            )
        if (self.nota_maxima - self.nota_minima) % self.passo != 0:
            raise EscalaAvaliacaoInvalidaError(
                "O intervalo entre nota mínima e máxima deve ser múltiplo do passo."
            )

    def validar(self, nota: Nota) -> None:
        """Levanta `NotaForaDaEscalaError` se a nota não respeitar esta escala."""
        if nota.valor < self.nota_minima or nota.valor > self.nota_maxima:
            raise NotaForaDaEscalaError(
                f"Nota {nota.valor} fora da escala permitida "
                f"[{self.nota_minima}, {self.nota_maxima}]."
            )
        if (nota.valor - self.nota_minima) % self.passo != 0:
            raise NotaForaDaEscalaError(
                f"Nota {nota.valor} não respeita o passo de {self.passo} da escala."
            )

    @classmethod
    def padrao(cls) -> "EscalaAvaliacao":
        """Escala padrão do Filmes e Cubos: 0,5 a 5,0 em passos de 0,5."""
        return cls(
            nota_minima=Decimal("0.5"),
            nota_maxima=Decimal("5.0"),
            passo=Decimal("0.5"),
        )
