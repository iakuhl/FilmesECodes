"""Contrato de persistência para a entidade CategoriaOscar."""

from typing import Protocol

from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, TemporadaOscarId


class CategoriaOscarRepository(Protocol):
    def salvar(self, categoria: CategoriaOscar) -> None: ...

    def buscar_por_id(self, categoria_id: CategoriaOscarId) -> CategoriaOscar | None: ...

    def listar_por_temporada(self, temporada_id: TemporadaOscarId) -> list[CategoriaOscar]: ...
