"""Entidade que representa uma categoria de premiação de uma temporada do Óscar."""

from __future__ import annotations

from uuid import uuid4

from filmes_e_cubos.domain.exceptions.oscar import NomeCategoriaObrigatorioError
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


class CategoriaOscar:
    """Uma categoria de premiação (fixa ou variável) dentro de uma temporada do Óscar."""

    def __init__(
        self,
        *,
        id: CategoriaOscarId,
        temporada_id: TemporadaOscarId,
        nome: str,
        tipo: TipoCategoriaOscar,
        descricao: str | None = None,
    ) -> None:
        if not nome or not nome.strip():
            raise NomeCategoriaObrigatorioError("O nome da categoria é obrigatório.")
        self._id = id
        self._temporada_id = temporada_id
        self._nome = nome
        self._tipo = tipo
        self._descricao = descricao

    @classmethod
    def criar(
        cls,
        *,
        temporada_id: TemporadaOscarId,
        nome: str,
        tipo: TipoCategoriaOscar,
        descricao: str | None = None,
    ) -> CategoriaOscar:
        return cls(
            id=CategoriaOscarId(uuid4()),
            temporada_id=temporada_id,
            nome=nome,
            tipo=tipo,
            descricao=descricao,
        )

    @property
    def id(self) -> CategoriaOscarId:
        return self._id

    @property
    def temporada_id(self) -> TemporadaOscarId:
        return self._temporada_id

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def tipo(self) -> TipoCategoriaOscar:
        return self._tipo

    @property
    def descricao(self) -> str | None:
        return self._descricao
