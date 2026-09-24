"""Exceção base compartilhada por todo o domínio."""


class DomainError(Exception):
    """Classe base de toda exceção levantada por violação de invariante do domínio."""


class EntidadeNaoEncontradaError(DomainError):
    """Levantada quando uma entidade referenciada por id não é encontrada.

    Reutilizada por todos os casos de uso (em vez de uma subclasse por
    entidade) porque o tratamento é sempre o mesmo: a operação não pode
    prosseguir sem a entidade referenciada existir.
    """
