"""Contrato de persistência para a entidade Indicacao."""

from typing import Protocol

from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, IndicacaoId, RodadaId


class IndicacaoRepository(Protocol):
    def salvar(self, indicacao: Indicacao) -> None: ...

    def buscar_por_id(self, indicacao_id: IndicacaoId) -> Indicacao | None: ...

    def listar_por_rodada(self, rodada_id: RodadaId) -> list[Indicacao]: ...

    def listar_assistidas_por_filme(self, filme_id: FilmeId) -> list[Indicacao]: ...

    def listar_por_filme(self, filme_id: FilmeId) -> list[Indicacao]:
        """Todas as indicações do filme, de qualquer clube e em qualquer situação."""
        ...
