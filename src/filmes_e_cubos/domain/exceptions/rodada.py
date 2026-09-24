"""Exceções relacionadas à entidade Rodada."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class RodadaJaAbertaError(DomainError):
    """Levantada ao tentar abrir uma nova rodada enquanto outra já está aberta."""


class RodadaJaEncerradaError(DomainError):
    """Levantada ao tentar operar sobre uma rodada que já foi encerrada."""


class RodadaNaoEncerravelError(DomainError):
    """Levantada ao tentar encerrar uma rodada com indicações ainda não assistidas."""


class RodadaLotadaError(DomainError):
    """Levantada ao tentar adicionar uma indicação além do tamanho configurado da rodada."""
