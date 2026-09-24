"""Implementação in-memory de `AvaliacaoRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.value_objects.identificadores import (
    AvaliacaoId,
    MembroId,
    SessaoExibicaoId,
)


class AvaliacaoRepositorioFake:
    def __init__(self) -> None:
        self._avaliacoes: dict[AvaliacaoId, Avaliacao] = {}

    def salvar(self, avaliacao: Avaliacao) -> None:
        self._avaliacoes[avaliacao.id] = avaliacao

    def listar_por_sessao(self, sessao_id: SessaoExibicaoId) -> list[Avaliacao]:
        return [
            avaliacao for avaliacao in self._avaliacoes.values() if avaliacao.sessao_id == sessao_id
        ]

    def buscar_por_sessao_e_membro(
        self, sessao_id: SessaoExibicaoId, membro_id: MembroId
    ) -> Avaliacao | None:
        for avaliacao in self._avaliacoes.values():
            if avaliacao.sessao_id == sessao_id and avaliacao.membro_id == membro_id:
                return avaliacao
        return None
