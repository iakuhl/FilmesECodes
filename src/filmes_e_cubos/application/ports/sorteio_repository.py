"""Contrato de persistência para a entidade Sorteio."""

from typing import Protocol

from filmes_e_cubos.domain.entities.sorteio import Sorteio
from filmes_e_cubos.domain.value_objects.identificadores import RodadaId


class SorteioRepository(Protocol):
    def salvar(self, sorteio: Sorteio) -> None: ...

    def listar_por_rodada(self, rodada_id: RodadaId) -> list[Sorteio]: ...
