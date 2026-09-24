"""Contrato de persistência para a entidade TemporadaOscar."""

from typing import Protocol

from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, TemporadaOscarId


class TemporadaOscarRepository(Protocol):
    def salvar(self, temporada: TemporadaOscar) -> None: ...

    def buscar_por_id(self, temporada_id: TemporadaOscarId) -> TemporadaOscar | None: ...

    def buscar_por_clube_e_ano(self, clube_id: ClubeId, ano: int) -> TemporadaOscar | None: ...
