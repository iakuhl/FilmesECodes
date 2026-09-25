"""Caso de uso: abrir uma nova temporada (edição anual) do Óscar do clube."""

from __future__ import annotations

from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.domain.entities.temporada_oscar import (
    NOMEACOES_POR_CATEGORIA_PADRAO,
    TemporadaOscar,
)
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import TemporadaOscarDuplicadaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class AbrirTemporadaOscar:
    """Cria a edição do Óscar de um clube num ano — uma só por ano (decisão 6)."""

    def __init__(
        self,
        temporada_repository: TemporadaOscarRepository,
        clube_repository: ClubeRepository,
    ) -> None:
        self._temporadas = temporada_repository
        self._clubes = clube_repository

    def executar(
        self,
        *,
        clube_id: ClubeId,
        ano: int,
        nome: str,
        nomeacoes_por_categoria: int = NOMEACOES_POR_CATEGORIA_PADRAO,
    ) -> TemporadaOscar:
        if self._clubes.buscar_por_id(clube_id) is None:
            raise EntidadeNaoEncontradaError(f"Clube {clube_id} não encontrado.")
        if self._temporadas.buscar_por_clube_e_ano(clube_id, ano) is not None:
            raise TemporadaOscarDuplicadaError(f"O clube já tem uma edição do Óscar de {ano}.")
        temporada = TemporadaOscar.abrir(
            clube_id=clube_id,
            ano=ano,
            nome=nome,
            nomeacoes_por_categoria=nomeacoes_por_categoria,
        )
        self._temporadas.salvar(temporada)
        return temporada
