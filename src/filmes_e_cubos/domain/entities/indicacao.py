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
from filmes_e_cubos.domain.value_objects.tipo_indicacao import TipoIndicacao

_ORIGENS_VALIDAS_PARA_ASSISTIDA = (StatusIndicacao.PENDENTE, StatusIndicacao.SORTEADA)


class Indicacao:
    """O filme que um membro indicou (ou que o grupo escolheu, no caso de
    uma indicação DEMOCRACIA) para uma rodada específica.
    """

    def __init__(
        self,
        *,
        id: IndicacaoId,
        rodada_id: RodadaId,
        filme_id: FilmeId,
        data_indicacao: date,
        membro_id: MembroId | None = None,
        tipo: TipoIndicacao = TipoIndicacao.NORMAL,
        status: StatusIndicacao = StatusIndicacao.PENDENTE,
    ) -> None:
        self._id = id
        self._rodada_id = rodada_id
        self._membro_id = membro_id
        self._filme_id = filme_id
        self._data_indicacao = data_indicacao
        self._tipo = tipo
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
        """Cria uma indicação normal, sempre com um membro indicador."""
        return cls(
            id=IndicacaoId(uuid4()),
            rodada_id=rodada_id,
            membro_id=membro_id,
            filme_id=filme_id,
            data_indicacao=data_indicacao,
            tipo=TipoIndicacao.NORMAL,
        )

    @classmethod
    def criar_democracia(
        cls,
        *,
        rodada_id: RodadaId,
        filme_id: FilmeId,
        data_indicacao: date,
    ) -> Indicacao:
        """Cria uma indicação DEMOCRACIA: sessão extra escolhida em grupo,
        sem um membro indicador individual e fora da cota da rodada.
        """
        return cls(
            id=IndicacaoId(uuid4()),
            rodada_id=rodada_id,
            membro_id=None,
            filme_id=filme_id,
            data_indicacao=data_indicacao,
            tipo=TipoIndicacao.DEMOCRACIA,
        )

    @property
    def id(self) -> IndicacaoId:
        return self._id

    @property
    def rodada_id(self) -> RodadaId:
        return self._rodada_id

    @property
    def membro_id(self) -> MembroId | None:
        return self._membro_id

    @property
    def filme_id(self) -> FilmeId:
        return self._filme_id

    @property
    def data_indicacao(self) -> date:
        return self._data_indicacao

    @property
    def tipo(self) -> TipoIndicacao:
        return self._tipo

    @property
    def status(self) -> StatusIndicacao:
        return self._status

    def marcar_sorteada(self) -> None:
        """Transiciona a indicação de `PENDENTE` para `SORTEADA`.

        O sorteio é uma etapa opcional de apoio: nada obriga a indicação a
        passar por aqui antes de ser assistida (ver `marcar_assistida`).
        """
        if self._status is not StatusIndicacao.PENDENTE:
            raise TransicaoDeStatusInvalidaError(
                f"Só é possível sortear uma indicação pendente (status atual: {self._status})."
            )
        self._status = StatusIndicacao.SORTEADA

    def marcar_assistida(self) -> None:
        """Transiciona a indicação para `ASSISTIDA`, a partir de `PENDENTE`
        (sorteio pulado) ou de `SORTEADA` (fluxo com sorteio).
        """
        if self._status not in _ORIGENS_VALIDAS_PARA_ASSISTIDA:
            raise TransicaoDeStatusInvalidaError(
                f"Não é possível assistir uma indicação com status {self._status}."
            )
        self._status = StatusIndicacao.ASSISTIDA
