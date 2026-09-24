"""Status de uma avaliação: nota registrada ou membro dorminhoco."""

from enum import Enum, auto


class StatusAvaliacao(Enum):
    """NOTA_REGISTRADA é uma avaliação com nota válida. DORMINHOCO é o
    registro de que o membro esteve presente na sessão mas cochilou e não
    tem uma nota a dar — o "voto" fica registrado para a posteridade, mas
    deve ser ignorado em qualquer cálculo de média.
    """

    NOTA_REGISTRADA = auto()
    DORMINHOCO = auto()
