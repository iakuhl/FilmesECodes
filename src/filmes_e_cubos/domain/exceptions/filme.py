"""Exceções relacionadas à entidade Filme."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class TituloFilmeObrigatorioError(DomainError):
    """Levantada quando um filme é criado sem título."""


class DuracaoFilmeInvalidaError(DomainError):
    """Levantada quando a duração informada para um filme não é um número positivo de minutos."""
