"""Implementação in-memory de `CategoriaOscarRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, TemporadaOscarId


class CategoriaOscarRepositorioFake:
    def __init__(self) -> None:
        self._categorias: dict[CategoriaOscarId, CategoriaOscar] = {}

    def salvar(self, categoria: CategoriaOscar) -> None:
        self._categorias[categoria.id] = categoria

    def buscar_por_id(self, categoria_id: CategoriaOscarId) -> CategoriaOscar | None:
        return self._categorias.get(categoria_id)

    def listar_por_temporada(self, temporada_id: TemporadaOscarId) -> list[CategoriaOscar]:
        return [
            categoria
            for categoria in self._categorias.values()
            if categoria.temporada_id == temporada_id
        ]
