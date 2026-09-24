"""Exceções relacionadas à entidade Membro."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class NomeMembroObrigatorioError(DomainError):
    """Levantada quando um membro é criado sem nome."""


class MembroInativoError(DomainError):
    """Levantada ao tentar, em nome de um membro inativo, uma ação que exige membro ativo."""
