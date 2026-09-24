"""Implementação in-memory de `MembroRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, MembroId


class MembroRepositorioFake:
    def __init__(self) -> None:
        self._membros: dict[MembroId, Membro] = {}

    def salvar(self, membro: Membro) -> None:
        self._membros[membro.id] = membro

    def buscar_por_id(self, membro_id: MembroId) -> Membro | None:
        return self._membros.get(membro_id)

    def listar_ativos_por_clube(self, clube_id: ClubeId) -> list[Membro]:
        return [
            membro
            for membro in self._membros.values()
            if membro.clube_id == clube_id and membro.ativo
        ]
