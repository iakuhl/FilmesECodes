"""Contrato de persistência para a entidade Membro."""

from typing import Protocol

from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, MembroId


class MembroRepository(Protocol):
    def salvar(self, membro: Membro) -> None: ...

    def buscar_por_id(self, membro_id: MembroId) -> Membro | None: ...

    def listar_ativos_por_clube(self, clube_id: ClubeId) -> list[Membro]: ...

    def listar_por_clube(self, clube_id: ClubeId) -> list[Membro]: ...
