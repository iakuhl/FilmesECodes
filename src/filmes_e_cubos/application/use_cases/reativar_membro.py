"""Caso de uso: reativar um membro que tinha sido desativado."""

from __future__ import annotations

from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId


class ReativarMembro:
    """Devolve um membro inativo às rodadas, com o histórico que ele já tinha."""

    def __init__(self, membro_repository: MembroRepository) -> None:
        self._membros = membro_repository

    def executar(self, *, membro_id: MembroId) -> None:
        membro = self._membros.buscar_por_id(membro_id)
        if membro is None:
            raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado.")
        membro.reativar()
        self._membros.salvar(membro)
