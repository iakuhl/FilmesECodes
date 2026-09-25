"""Contrato de persistência para a entidade VotacaoOscar."""

from typing import Protocol

from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId


class VotacaoOscarRepository(Protocol):
    def salvar(self, votacao: VotacaoOscar) -> None: ...

    def buscar_por_temporada(self, temporada_id: TemporadaOscarId) -> VotacaoOscar | None: ...
