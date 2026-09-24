"""Entidade que representa a indicação de um filme por um membro em uma rodada."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.indicacao import TransicaoDeStatusInvalidaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    FilmeId,
    IndicacaoId,
    MembroId,
    RodadaId,
)
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao


class Indicacao:
    """O filme que um membro indicou para uma rodada específica."""

    def __init__(
        self,
        *,
        id: IndicacaoId,
        rodada_id: RodadaId,
        membro_id: MembroId,
        filme_id: FilmeId,
        data_indicacao: date,
        status: StatusIndicacao = StatusIndicacao.PENDENTE,
    ) -> None:
        self._id = id
        self._rodada_id = rodada_id
        self._membro_id = membro_id
        self._filme_id = filme_id
        self._data_indicacao = data_indicacao
        self._status = status

    @classmethod
    def criar(
        cls,
        *,
        rodada_id: RodadaId,
        membro_id: MembroId,
        filme_id: FilmeId,
        data_indicacao: date,
    ) -> Indicacao:
        return cls(
            id=IndicacaoId(uuid4()),
            rodada_id=rodada_id,
            membro_id=membro_id,
            filme_id=filme_id,
            data_indicacao=data_indicacao,
        )

    @property
    def id(self) -> IndicacaoId:
        return self._id

    @property
    def rodada_id(self) -> RodadaId:
        return self._rodada_id

    @property
    def membro_id(self) -> MembroId:
        return self._membro_id

    @property
    def filme_id(self) -> FilmeId:
        return self._filme_id

    @property
    def data_indicacao(self) -> date:
        return self._data_indicacao

    @property
    def status(self) -> StatusIndicacao:
        return self._status

    def marcar_sorteada(self) -> None:
        """Transiciona a indicação de `PENDENTE` para `SORTEADA`."""
        if self._status is not StatusIndicacao.PENDENTE:
            raise TransicaoDeStatusInvalidaError(
                f"Só é possível sortear uma indicação pendente (status atual: {self._status})."
            )
        self._status = StatusIndicacao.SORTEADA

    def marcar_assistida(self) -> None:
        """Transiciona a indicação de `SORTEADA` para `ASSISTIDA`."""
        if self._status is not StatusIndicacao.SORTEADA:
            raise TransicaoDeStatusInvalidaError(
                f"Só é possível assistir uma indicação sorteada (status atual: {self._status})."
            )
        self._status = StatusIndicacao.ASSISTIDA
