"""Contrato de persistência para a entidade Trofeu."""

from typing import Protocol

from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId


class TrofeuRepository(Protocol):
    def salvar(self, trofeu: Trofeu) -> None: ...

    def buscar_por_categoria(self, categoria_id: CategoriaOscarId) -> Trofeu | None: ...
