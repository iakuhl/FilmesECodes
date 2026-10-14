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
    """Levantada ao registrar o vencedor de uma categoria que já tem troféu."""


class NomeacaoInvalidaError(DomainError):
    """Levantada quando a nomeação vencedora informada não concorre na categoria."""


class EscolhaDoGrupoNecessariaError(DomainError):
    """Levantada ao registrar o vencedor sem o membro escolhido pelo grupo, quando ele é
    necessário: vitória de um filme democracia (sem indicador) ou empate absoluto.
    """


class MembroDeOutroClubeError(DomainError):
    """Levantada quando o membro escolhido pelo grupo não é do clube da edição."""


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


class VotoInvalidoError(DomainError):
    """Levantada quando as escolhas de um voto não servem ao turno da categoria
    (quantidade errada, nomeação repetida ou fora das candidatas).
    """


class CedulaConfirmadaError(DomainError):
    """Levantada ao alterar ou confirmar de novo uma cédula já confirmada."""


class CedulaIncompletaError(DomainError):
    """Levantada ao confirmar uma cédula sem voto em todas as categorias do turno."""


class MembroForaDaVotacaoError(DomainError):
    """Levantada quando quem vota não está entre os eleitores definidos no início da votação."""


class CategoriaForaDoTurnoError(DomainError):
    """Levantada ao votar numa categoria que não está em disputa no turno atual."""


class VotacaoEncerradaError(DomainError):
    """Levantada ao votar, confirmar ou apurar depois de a votação (ou o turno) terminar."""


class VotacaoEmAndamentoError(DomainError):
    """Levantada quando uma ação precisa da votação terminada (ex.: enviar o placar)."""
