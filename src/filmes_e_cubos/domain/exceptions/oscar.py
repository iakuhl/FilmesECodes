"""Exceções relacionadas ao Óscar do Filmes e Cubos (temporadas, categorias, apuração)."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class NomeCategoriaObrigatorioError(DomainError):
    """Levantada quando uma categoria do Óscar é criada sem nome."""


class TemporadaOscarInvalidaError(DomainError):
    """Levantada quando uma temporada do Óscar tenta uma transição de status inválida."""


class FilmeNaoAssistidoError(DomainError):
    """Levantada ao nomear, para uma categoria, um filme que o clube nunca assistiu."""


class FilmeNaoAssistidoNoAnoDaTemporadaError(DomainError):
    """Levantada ao nomear, para uma categoria, um filme assistido fora do ano da temporada."""


class CategoriaJaApuradaError(DomainError):
    """Levantada ao tentar apurar novamente uma categoria que já tem um troféu emitido."""


class NomeacaoInvalidaError(DomainError):
    """Levantada quando a nomeação vencedora de uma apuração não pertence à categoria apurada."""


class VencedorDemocraciaNaoInformadoError(DomainError):
    """Levantada ao apurar uma categoria cuja nomeação vencedora não tem indicador automático
    (veio de um filme DEMOCRACIA) sem que um vencedor manual tenha sido informado.
    """
