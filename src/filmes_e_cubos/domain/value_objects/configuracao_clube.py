"""Value object com os parâmetros de configuração de um clube."""

from dataclasses import dataclass

from filmes_e_cubos.domain.exceptions.clube import TamanhoRodadaInvalidoError
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao


@dataclass(frozen=True, slots=True)
class ConfiguracaoClube:
    """Parâmetros de negócio configuráveis de um clube."""

    tamanho_rodada: int
    escala_avaliacao: EscalaAvaliacao

    def __post_init__(self) -> None:
        if self.tamanho_rodada <= 0:
            raise TamanhoRodadaInvalidoError(
                f"Tamanho de rodada deve ser positivo, recebido: {self.tamanho_rodada}"
            )

    @classmethod
    def padrao(cls) -> "ConfiguracaoClube":
        """Configuração padrão do Filmes e Cubos: rodadas de 5 indicações."""
        return cls(tamanho_rodada=5, escala_avaliacao=EscalaAvaliacao.padrao())
