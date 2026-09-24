"""Implementação in-memory de `SessaoRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, SessaoExibicaoId


class SessaoRepositorioFake:
    def __init__(self) -> None:
        self._sessoes: dict[SessaoExibicaoId, SessaoExibicao] = {}

    def salvar(self, sessao: SessaoExibicao) -> None:
        self._sessoes[sessao.id] = sessao

    def buscar_por_id(self, sessao_id: SessaoExibicaoId) -> SessaoExibicao | None:
        return self._sessoes.get(sessao_id)

    def buscar_por_indicacao(self, indicacao_id: IndicacaoId) -> SessaoExibicao | None:
        for sessao in self._sessoes.values():
            if sessao.indicacao_id == indicacao_id:
                return sessao
        return None
