"""Caso de uso: desativar um membro do clube, preservando seu histórico."""

from __future__ import annotations

from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId


class DesativarMembro:
    """Marca um membro como inativo sem apagar seus registros passados."""

    def __init__(self, membro_repository: MembroRepository) -> None:
        self._membros = membro_repository

    def executar(self, *, membro_id: MembroId) -> None:
        membro = self._membros.buscar_por_id(membro_id)
        if membro is None:
            raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado.")
        membro.desativar()
        self._membros.salvar(membro)
