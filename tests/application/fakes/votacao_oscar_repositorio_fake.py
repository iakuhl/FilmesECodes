"""Implementação in-memory de `VotacaoOscarRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId


class VotacaoOscarRepositorioFake:
    def __init__(self) -> None:
        self._votacoes: dict[TemporadaOscarId, VotacaoOscar] = {}

    def salvar(self, votacao: VotacaoOscar) -> None:
        self._votacoes[votacao.temporada_id] = votacao

    def buscar_por_temporada(self, temporada_id: TemporadaOscarId) -> VotacaoOscar | None:
        return self._votacoes.get(temporada_id)
