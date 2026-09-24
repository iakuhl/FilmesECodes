"""Contrato de persistência para a entidade NomeacaoOscar."""

from typing import Protocol

from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, NomeacaoOscarId


class NomeacaoOscarRepository(Protocol):
    def salvar(self, nomeacao: NomeacaoOscar) -> None: ...

    def buscar_por_id(self, nomeacao_id: NomeacaoOscarId) -> NomeacaoOscar | None: ...

    def listar_por_categoria(self, categoria_id: CategoriaOscarId) -> list[NomeacaoOscar]: ...
