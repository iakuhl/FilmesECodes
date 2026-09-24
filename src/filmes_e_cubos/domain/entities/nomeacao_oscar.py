"""Entidade que representa um filme concorrendo em uma categoria do Óscar."""

from __future__ import annotations

from uuid import uuid4

from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    NomeacaoOscarId,
)


class NomeacaoOscar:
    """Um filme nomeado a uma categoria, rastreando quem o indicou originalmente.

    `indicado_por_membro_id` é herdado da `Indicacao` semanal original do
    filme (ver caso de uso `IndicarFilmeParaCategoria`) — é essa
    rastreabilidade que permite entregar o troféu a quem indicou o filme.
    Fica `None` quando o filme veio de uma indicação DEMOCRACIA (sem
    indicador individual); nesse caso, quem recebe o troféu é decidido
    pelo grupo no momento da apuração (ver `ApurarCategoriaOscar`).
    """

    def __init__(
        self,
        *,
        id: NomeacaoOscarId,
        categoria_id: CategoriaOscarId,
        filme_id: FilmeId,
        indicado_por_membro_id: MembroId | None,
    ) -> None:
        self._id = id
        self._categoria_id = categoria_id
        self._filme_id = filme_id
        self._indicado_por_membro_id = indicado_por_membro_id

    @classmethod
    def criar(
        cls,
        *,
        categoria_id: CategoriaOscarId,
        filme_id: FilmeId,
        indicado_por_membro_id: MembroId | None,
    ) -> NomeacaoOscar:
        return cls(
            id=NomeacaoOscarId(uuid4()),
            categoria_id=categoria_id,
            filme_id=filme_id,
            indicado_por_membro_id=indicado_por_membro_id,
        )

    @property
    def id(self) -> NomeacaoOscarId:
        return self._id

    @property
    def categoria_id(self) -> CategoriaOscarId:
        return self._categoria_id

    @property
    def filme_id(self) -> FilmeId:
        return self._filme_id

    @property
    def indicado_por_membro_id(self) -> MembroId | None:
        return self._indicado_por_membro_id
