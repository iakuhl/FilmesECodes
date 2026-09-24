"""Caso de uso: cadastrar um novo membro em um clube."""

from __future__ import annotations

from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class CadastrarMembro:
    """Adiciona um novo membro, ativo, a um clube existente."""

    def __init__(
        self,
        membro_repository: MembroRepository,
        clube_repository: ClubeRepository,
        relogio: RelogioService,
    ) -> None:
        self._membros = membro_repository
        self._clubes = clube_repository
        self._relogio = relogio

    def executar(self, *, clube_id: ClubeId, nome: str, apelido: str | None = None) -> Membro:
        if self._clubes.buscar_por_id(clube_id) is None:
            raise EntidadeNaoEncontradaError(f"Clube {clube_id} não encontrado.")
        membro = Membro.criar(
            clube_id=clube_id,
            nome=nome,
            apelido=apelido,
            data_ingresso=self._relogio.hoje(),
        )
        self._membros.salvar(membro)
        return membro
