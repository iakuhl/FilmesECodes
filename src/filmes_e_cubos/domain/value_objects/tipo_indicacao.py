"""Classificação de uma indicação: normal (semanal) ou democracia (extra)."""

from enum import Enum, auto


class TipoIndicacao(Enum):
    """NORMAL é a indicação semanal de um membro. DEMOCRACIA é uma sessão
    extra, decidida em grupo, para quando a sessão programada precisa ser
    adiada — não substitui a indicação normal da semana, é adicional a
    ela, e por isso não conta na cota de indicações da rodada nem exige
    um membro individual como indicador.
    """

    NORMAL = auto()
    DEMOCRACIA = auto()
