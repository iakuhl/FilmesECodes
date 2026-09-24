"""Contrato de persistência para a entidade SessaoExibicao."""

from typing import Protocol

from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, SessaoExibicaoId


class SessaoRepository(Protocol):
    def salvar(self, sessao: SessaoExibicao) -> None: ...

    def buscar_por_id(self, sessao_id: SessaoExibicaoId) -> SessaoExibicao | None: ...

    def buscar_por_indicacao(self, indicacao_id: IndicacaoId) -> SessaoExibicao | None: ...
