"""Caso de uso: abrir uma nova temporada (edição anual) do Óscar do clube."""

from __future__ import annotations

from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class AbrirTemporadaOscar:
    """Cria uma nova edição do Óscar do Filmes e Cubos para um clube e ano."""

    def __init__(
        self,
        temporada_repository: TemporadaOscarRepository,
        clube_repository: ClubeRepository,
    ) -> None:
        self._temporadas = temporada_repository
        self._clubes = clube_repository

    def executar(self, *, clube_id: ClubeId, ano: int, nome: str) -> TemporadaOscar:
        if self._clubes.buscar_por_id(clube_id) is None:
            raise EntidadeNaoEncontradaError(f"Clube {clube_id} não encontrado.")
        temporada = TemporadaOscar.abrir(clube_id=clube_id, ano=ano, nome=nome)
        self._temporadas.salvar(temporada)
        return temporada
