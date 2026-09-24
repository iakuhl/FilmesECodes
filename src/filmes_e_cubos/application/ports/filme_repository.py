"""Contrato de persistência para a entidade Filme."""

from typing import Protocol

from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId


class FilmeRepository(Protocol):
    def salvar(self, filme: Filme) -> None: ...

    def buscar_por_id(self, filme_id: FilmeId) -> Filme | None: ...
