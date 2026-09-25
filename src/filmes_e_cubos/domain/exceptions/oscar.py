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


class AcaoForaDaFaseError(DomainError):
    """Levantada ao tentar uma ação que a fase atual da edição do Óscar não permite
    (ex.: mudar qualquer coisa numa edição encerrada).
    """


class NumeroDeNomeacoesInvalidoError(DomainError):
    """Levantada ao abrir uma edição com menos nomeações por categoria do que a votação pede."""


class TemporadaOscarDuplicadaError(DomainError):
    """Levantada ao abrir uma segunda edição do Óscar para o mesmo clube e ano."""


class CategoriaCompletaError(DomainError):
    """Levantada ao nomear um filme para uma categoria que já tem todas as nomeações da edição."""


class TemporadaIncompletaError(DomainError):
    """Levantada ao avançar uma edição que ainda não cumpriu o que a fase atual exige
    (ex.: ir à votação com categorias sem todas as nomeações).
    """
