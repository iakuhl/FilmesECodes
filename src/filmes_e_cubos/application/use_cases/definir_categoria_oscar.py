"""Caso de uso: adicionar uma categoria de premiação a uma temporada do Óscar."""

from __future__ import annotations

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


class DefinirCategoriaOscar:
    """Adiciona uma categoria (fixa ou variável) a uma temporada do Óscar."""

    def __init__(
        self,
        categoria_repository: CategoriaOscarRepository,
        temporada_repository: TemporadaOscarRepository,
    ) -> None:
        self._categorias = categoria_repository
        self._temporadas = temporada_repository

    def executar(
        self,
        *,
        temporada_id: TemporadaOscarId,
        nome: str,
        tipo: TipoCategoriaOscar,
        descricao: str | None = None,
    ) -> CategoriaOscar:
        if self._temporadas.buscar_por_id(temporada_id) is None:
            raise EntidadeNaoEncontradaError(f"Temporada {temporada_id} não encontrada.")
        categoria = CategoriaOscar.criar(
            temporada_id=temporada_id, nome=nome, tipo=tipo, descricao=descricao
        )
        self._categorias.salvar(categoria)
        return categoria
