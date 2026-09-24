"""Implementação in-memory de `IndicacaoRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, IndicacaoId, RodadaId
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao


class IndicacaoRepositorioFake:
    def __init__(self) -> None:
        self._indicacoes: dict[IndicacaoId, Indicacao] = {}

    def salvar(self, indicacao: Indicacao) -> None:
        self._indicacoes[indicacao.id] = indicacao

    def buscar_por_id(self, indicacao_id: IndicacaoId) -> Indicacao | None:
        return self._indicacoes.get(indicacao_id)

    def listar_por_rodada(self, rodada_id: RodadaId) -> list[Indicacao]:
        return [
            indicacao for indicacao in self._indicacoes.values() if indicacao.rodada_id == rodada_id
        ]

    def buscar_assistida_por_filme(self, filme_id: FilmeId) -> Indicacao | None:
        for indicacao in self._indicacoes.values():
            if indicacao.filme_id == filme_id and indicacao.status is StatusIndicacao.ASSISTIDA:
                return indicacao
        return None
