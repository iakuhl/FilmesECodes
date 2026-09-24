"""Implementação in-memory de `NomeacaoOscarRepository`, para uso em testes."""

from __future__ import annotations

from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, NomeacaoOscarId


class NomeacaoOscarRepositorioFake:
    def __init__(self) -> None:
        self._nomeacoes: dict[NomeacaoOscarId, NomeacaoOscar] = {}

    def salvar(self, nomeacao: NomeacaoOscar) -> None:
        self._nomeacoes[nomeacao.id] = nomeacao

    def buscar_por_id(self, nomeacao_id: NomeacaoOscarId) -> NomeacaoOscar | None:
        return self._nomeacoes.get(nomeacao_id)

    def listar_por_categoria(self, categoria_id: CategoriaOscarId) -> list[NomeacaoOscar]:
        return [
            nomeacao
            for nomeacao in self._nomeacoes.values()
            if nomeacao.categoria_id == categoria_id
        ]
