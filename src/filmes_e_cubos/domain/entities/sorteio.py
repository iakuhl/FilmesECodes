"""Entidade que registra o sorteio de uma indicação dentro de uma rodada."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from filmes_e_cubos.domain.value_objects.identificadores import (
    IndicacaoId,
    RodadaId,
    SorteioId,
)


class Sorteio:
    """Registro histórico de qual indicação foi sorteada para a próxima sessão."""

    def __init__(
        self,
        *,
        id: SorteioId,
        rodada_id: RodadaId,
        indicacao_sorteada_id: IndicacaoId,
        data_sorteio: datetime,
        metodo: str,
    ) -> None:
        self._id = id
        self._rodada_id = rodada_id
        self._indicacao_sorteada_id = indicacao_sorteada_id
        self._data_sorteio = data_sorteio
        self._metodo = metodo

    @classmethod
    def registrar(
        cls,
        *,
        rodada_id: RodadaId,
        indicacao_sorteada_id: IndicacaoId,
        data_sorteio: datetime,
        metodo: str,
    ) -> Sorteio:
        return cls(
            id=SorteioId(uuid4()),
            rodada_id=rodada_id,
            indicacao_sorteada_id=indicacao_sorteada_id,
            data_sorteio=data_sorteio,
            metodo=metodo,
        )

    @property
    def id(self) -> SorteioId:
        return self._id

    @property
    def rodada_id(self) -> RodadaId:
        return self._rodada_id

    @property
    def indicacao_sorteada_id(self) -> IndicacaoId:
        return self._indicacao_sorteada_id

    @property
    def data_sorteio(self) -> datetime:
        return self._data_sorteio

    @property
    def metodo(self) -> str:
        return self._metodo
