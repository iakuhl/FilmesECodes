"""Implementação in-memory de `TurnoDeVotacaoRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, TurnoDeVotacaoId


class TurnoDeVotacaoRepositorioFake:
    def __init__(self) -> None:
        self._turnos: dict[TurnoDeVotacaoId, TurnoDeVotacao] = {}

    def salvar(self, turno: TurnoDeVotacao) -> None:
        self._turnos[turno.id] = turno

    def listar_por_categoria(self, categoria_id: CategoriaOscarId) -> list[TurnoDeVotacao]:
        return sorted(
            (turno for turno in self._turnos.values() if turno.categoria_id == categoria_id),
            key=lambda turno: turno.numero,
        )
