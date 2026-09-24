"""Implementação in-memory de `ClubeRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class ClubeRepositorioFake:
    def __init__(self) -> None:
        self._clubes: dict[ClubeId, Clube] = {}

    def salvar(self, clube: Clube) -> None:
        self._clubes[clube.id] = clube

    def buscar_por_id(self, clube_id: ClubeId) -> Clube | None:
        return self._clubes.get(clube_id)

    def listar_todos(self) -> list[Clube]:
        return list(self._clubes.values())
