"""Exceções relacionadas à entidade Indicacao."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class IndicacaoDuplicadaError(DomainError):
    """Levantada quando um membro tenta indicar mais de um filme na mesma rodada."""


class TransicaoDeStatusInvalidaError(DomainError):
    """Levantada quando uma indicação tenta uma transição de status não permitida."""
