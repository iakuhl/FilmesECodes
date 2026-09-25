"""Contrato de persistência para a entidade Cedula."""

from typing import Protocol

from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, VotacaoOscarId


class CedulaRepository(Protocol):
    def salvar(self, cedula: Cedula) -> None: ...

    def buscar(self, votacao_id: VotacaoOscarId, turno: int, membro_id: MembroId) -> Cedula | None:
        """A cédula do eleitor naquele turno da votação, se ele já votou."""
        ...

    def listar_por_turno(self, votacao_id: VotacaoOscarId, turno: int) -> list[Cedula]: ...
