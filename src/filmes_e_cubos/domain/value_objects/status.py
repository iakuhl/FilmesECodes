"""Enumerações de status usadas pelas entidades do domínio."""

from enum import Enum, auto


class StatusRodada(Enum):
    ABERTA = auto()
    ENCERRADA = auto()


class StatusIndicacao(Enum):
    PENDENTE = auto()
    SORTEADA = auto()
    ASSISTIDA = auto()


class StatusTemporadaOscar(Enum):
    EM_PREPARACAO = auto()
    ABERTA_PARA_INDICACOES = auto()
    EM_VOTACAO = auto()
    APURADA = auto()
    ENCERRADA = auto()


class TipoCategoriaOscar(Enum):
    FIXA = auto()
    VARIAVEL = auto()


class ModoDeVotacao(Enum):
    """Como um turno da votação do Óscar conta os votos (decisões 8.1, 8.5 e 16)."""

    DUPLA = auto()
    """Cada eleitor dá uma 1ª opção (2 pontos) e uma 2ª opção (1 ponto)."""

    CLASSIFICACAO = auto()
    """Cada eleitor ordena as X candidatas, que recebem X, X-1, ..., 1 pontos."""
