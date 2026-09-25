"""Implementação in-memory de `CedulaRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.value_objects.identificadores import (
    CedulaId,
    MembroId,
    VotacaoOscarId,
)


class CedulaRepositorioFake:
    def __init__(self) -> None:
        self._cedulas: dict[CedulaId, Cedula] = {}

    def salvar(self, cedula: Cedula) -> None:
        self._cedulas[cedula.id] = cedula

    def buscar(self, votacao_id: VotacaoOscarId, turno: int, membro_id: MembroId) -> Cedula | None:
        for cedula in self.listar_por_turno(votacao_id, turno):
            if cedula.membro_id == membro_id:
                return cedula
        return None

    def listar_por_turno(self, votacao_id: VotacaoOscarId, turno: int) -> list[Cedula]:
        return [
            cedula
            for cedula in self._cedulas.values()
            if cedula.votacao_id == votacao_id and cedula.turno == turno
        ]
