"""Caso de uso: marcar o dia da cerimônia de uma edição do Óscar."""

from __future__ import annotations

from datetime import date

from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId


class DefinirDataEventoOscar:
    """Define (ou remarca) a data do evento de uma edição que ainda não foi encerrada."""

    def __init__(self, temporada_repository: TemporadaOscarRepository) -> None:
        self._temporadas = temporada_repository

    def executar(self, *, temporada_id: TemporadaOscarId, data_evento: date) -> TemporadaOscar:
        temporada = self._temporadas.buscar_por_id(temporada_id)
        if temporada is None:
            raise EntidadeNaoEncontradaError(f"Temporada {temporada_id} não encontrada.")
        temporada.definir_data_evento(data_evento)
        self._temporadas.salvar(temporada)
        return temporada
