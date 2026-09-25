"""Exceções relacionadas a notas e avaliações."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class NotaInvalidaError(DomainError):
    """Levantada quando o valor de uma nota é numericamente inválido."""


class EscalaAvaliacaoInvalidaError(DomainError):
    """Levantada quando os parâmetros de uma escala de avaliação são inconsistentes."""


class NotaForaDaEscalaError(DomainError):
    """Levantada quando uma nota não respeita a escala de avaliação do clube."""


class AvaliacaoDuplicadaError(DomainError):
    """Levantada quando um membro tenta avaliar a mesma sessão mais de uma vez."""


class MembroAusenteNaSessaoError(DomainError):
    """Levantada quando alguém que não esteve presente na sessão tenta avaliá-la."""
