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
    APURADA = auto()
    ENCERRADA = auto()


class TipoCategoriaOscar(Enum):
    FIXA = auto()
    VARIAVEL = auto()
