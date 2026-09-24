"""Contrato de persistência para a entidade Avaliacao."""

from typing import Protocol

from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, SessaoExibicaoId


class AvaliacaoRepository(Protocol):
    def salvar(self, avaliacao: Avaliacao) -> None: ...

    def listar_por_sessao(self, sessao_id: SessaoExibicaoId) -> list[Avaliacao]: ...

    def buscar_por_sessao_e_membro(
        self, sessao_id: SessaoExibicaoId, membro_id: MembroId
    ) -> Avaliacao | None: ...
