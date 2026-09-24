"""Implementação in-memory de `RodadaRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, RodadaId


class RodadaRepositorioFake:
    def __init__(self) -> None:
        self._rodadas: dict[RodadaId, Rodada] = {}

    def salvar(self, rodada: Rodada) -> None:
        self._rodadas[rodada.id] = rodada

    def buscar_por_id(self, rodada_id: RodadaId) -> Rodada | None:
        return self._rodadas.get(rodada_id)

    def buscar_aberta_por_clube(self, clube_id: ClubeId) -> Rodada | None:
        for rodada in self._rodadas.values():
            if rodada.clube_id == clube_id and rodada.esta_aberta:
                return rodada
        return None

    def contar_por_clube(self, clube_id: ClubeId) -> int:
        return sum(1 for rodada in self._rodadas.values() if rodada.clube_id == clube_id)
