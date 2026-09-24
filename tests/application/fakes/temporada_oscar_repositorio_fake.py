"""Implementação in-memory de `TemporadaOscarRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, TemporadaOscarId


class TemporadaOscarRepositorioFake:
    def __init__(self) -> None:
        self._temporadas: dict[TemporadaOscarId, TemporadaOscar] = {}

    def salvar(self, temporada: TemporadaOscar) -> None:
        self._temporadas[temporada.id] = temporada

    def buscar_por_id(self, temporada_id: TemporadaOscarId) -> TemporadaOscar | None:
        return self._temporadas.get(temporada_id)

    def buscar_por_clube_e_ano(self, clube_id: ClubeId, ano: int) -> TemporadaOscar | None:
        for temporada in self._temporadas.values():
            if temporada.clube_id == clube_id and temporada.ano == ano:
                return temporada
        return None

    def listar_por_clube(self, clube_id: ClubeId) -> list[TemporadaOscar]:
        return [
            temporada for temporada in self._temporadas.values() if temporada.clube_id == clube_id
        ]
