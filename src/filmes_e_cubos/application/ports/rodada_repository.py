"""Contrato de persistência para a entidade Rodada."""

from typing import Protocol

from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, RodadaId


class RodadaRepository(Protocol):
    def salvar(self, rodada: Rodada) -> None: ...

    def buscar_por_id(self, rodada_id: RodadaId) -> Rodada | None: ...

    def buscar_aberta_por_clube(self, clube_id: ClubeId) -> Rodada | None: ...

    def contar_por_clube(self, clube_id: ClubeId) -> int: ...

    def listar_por_clube(self, clube_id: ClubeId) -> list[Rodada]:
        """Todas as rodadas do clube, da primeira à mais recente (por `numero`)."""
        ...
