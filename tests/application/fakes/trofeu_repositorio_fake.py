"""Implementação in-memory de `TrofeuRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId


class TrofeuRepositorioFake:
    def __init__(self) -> None:
        self._trofeus: list[Trofeu] = []

    def salvar(self, trofeu: Trofeu) -> None:
        self._trofeus.append(trofeu)

    def buscar_por_categoria(self, categoria_id: CategoriaOscarId) -> Trofeu | None:
        for trofeu in self._trofeus:
            if trofeu.categoria_id == categoria_id:
                return trofeu
        return None
