"""Entidade que representa a sessão em que o clube assistiu a um filme."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.value_objects.identificadores import (
    IndicacaoId,
    MembroId,
    SessaoExibicaoId,
)


class SessaoExibicao:
    """A sessão em que o clube efetivamente assistiu ao filme sorteado."""

    def __init__(
        self,
        *,
        id: SessaoExibicaoId,
        indicacao_id: IndicacaoId,
        data_sessao: date,
        membros_presentes: frozenset[MembroId],
    ) -> None:
        self._id = id
        self._indicacao_id = indicacao_id
        self._data_sessao = data_sessao
        self._membros_presentes = membros_presentes

    @classmethod
    def registrar(
        cls,
        *,
        indicacao_id: IndicacaoId,
        data_sessao: date,
        membros_presentes: frozenset[MembroId],
    ) -> SessaoExibicao:
        return cls(
            id=SessaoExibicaoId(uuid4()),
            indicacao_id=indicacao_id,
            data_sessao=data_sessao,
            membros_presentes=membros_presentes,
        )

    @property
    def id(self) -> SessaoExibicaoId:
        return self._id

    @property
    def indicacao_id(self) -> IndicacaoId:
        return self._indicacao_id

    @property
    def data_sessao(self) -> date:
        return self._data_sessao

    @property
    def membros_presentes(self) -> frozenset[MembroId]:
        return self._membros_presentes
