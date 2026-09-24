"""Exceções relacionadas ao agregado Clube e sua configuração."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class NomeClubeObrigatorioError(DomainError):
    """Levantada quando um clube é criado sem nome."""


class TamanhoRodadaInvalidoError(DomainError):
    """Levantada quando o tamanho de rodada configurado para o clube é inválido."""
