"""Implementação in-memory de `SorteioRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.sorteio import Sorteio
from filmes_e_cubos.domain.value_objects.identificadores import RodadaId


class SorteioRepositorioFake:
    def __init__(self) -> None:
        self._sorteios: list[Sorteio] = []

    def salvar(self, sorteio: Sorteio) -> None:
        self._sorteios.append(sorteio)

    def listar_por_rodada(self, rodada_id: RodadaId) -> list[Sorteio]:
        return [sorteio for sorteio in self._sorteios if sorteio.rodada_id == rodada_id]
