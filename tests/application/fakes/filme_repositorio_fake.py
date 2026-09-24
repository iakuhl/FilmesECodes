"""Implementação in-memory de `FilmeRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId


class FilmeRepositorioFake:
    def __init__(self) -> None:
        self._filmes: dict[FilmeId, Filme] = {}

    def salvar(self, filme: Filme) -> None:
        self._filmes[filme.id] = filme

    def buscar_por_id(self, filme_id: FilmeId) -> Filme | None:
        return self._filmes.get(filme_id)
