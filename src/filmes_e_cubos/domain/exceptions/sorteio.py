"""Exceções relacionadas ao sorteio de indicações."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class NenhumaIndicacaoElegivelError(DomainError):
    """Levantada ao tentar sortear uma rodada sem indicações pendentes."""


class IndicacaoNaoElegivelParaSorteioError(DomainError):
    """Levantada quando o resultado de um sorteio não pertence às indicações candidatas.

    Funciona como uma verificação defensiva na fronteira com `SorteadorService`:
    o domínio não confia cegamente no retorno de uma implementação externa.
    """
