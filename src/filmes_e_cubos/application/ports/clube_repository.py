"""Contrato de persistência para a entidade Clube."""

from typing import Protocol

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class ClubeRepository(Protocol):
    def salvar(self, clube: Clube) -> None: ...

    def buscar_por_id(self, clube_id: ClubeId) -> Clube | None: ...
