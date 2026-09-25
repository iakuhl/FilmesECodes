"""Entidade que representa a votação de uma edição do Óscar."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.oscar import (
    MembroForaDaVotacaoError,
    TemporadaIncompletaError,
    VotacaoEncerradaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    MembroId,
    TemporadaOscarId,
    VotacaoOscarId,
)


class VotacaoOscar:
    """A votação de uma edição: um evento com eleitores definidos (decisão 23).

    Começa quando a edição entra em votação, com os membros ativos do clube
    naquele momento, e os eleitores não mudam mais: desativar alguém não o
    tira da votação, e quem entra ou volta ao clube depois não vota.

    Corre em turnos. No 1º, toda categoria está em disputa; quando todos os
    eleitores confirmam as cédulas, o turno se encerra, e as categorias com
    o topo empatado passam ao turno seguinte (decisão 28). A votação
    termina no turno que não deixa empate a desfazer.
    """

    def __init__(
        self,
        *,
        id: VotacaoOscarId,
        temporada_id: TemporadaOscarId,
        eleitores: Iterable[MembroId],
        iniciada_em: datetime,
        turno_atual: int = 1,
        encerrada_em: datetime | None = None,
    ) -> None:
        self._id = id
        self._temporada_id = temporada_id
        self._eleitores = frozenset(eleitores)
        self._iniciada_em = iniciada_em
        self._turno_atual = turno_atual
        self._encerrada_em = encerrada_em

    @classmethod
    def iniciar(
        cls,
        *,
        temporada_id: TemporadaOscarId,
        eleitores: Iterable[MembroId],
        momento: datetime,
    ) -> VotacaoOscar:
        eleitores = frozenset(eleitores)
        if not eleitores:
            raise TemporadaIncompletaError("O clube não tem nenhum membro ativo para votar.")
        return cls(
            id=VotacaoOscarId(uuid4()),
            temporada_id=temporada_id,
            eleitores=eleitores,
            iniciada_em=momento,
        )

    @property
    def id(self) -> VotacaoOscarId:
        return self._id

    @property
    def temporada_id(self) -> TemporadaOscarId:
        return self._temporada_id

    @property
    def eleitores(self) -> frozenset[MembroId]:
        return self._eleitores

    @property
    def iniciada_em(self) -> datetime:
        return self._iniciada_em

    @property
    def turno_atual(self) -> int:
        return self._turno_atual

    @property
    def encerrada_em(self) -> datetime | None:
        return self._encerrada_em

    @property
    def encerrada(self) -> bool:
        return self._encerrada_em is not None

    def verificar_aberta(self) -> None:
        if self.encerrada:
            raise VotacaoEncerradaError("A votação desta edição já terminou.")

    def verificar_eleitor(self, membro_id: MembroId) -> None:
        if membro_id not in self._eleitores:
            raise MembroForaDaVotacaoError(
                f"Membro {membro_id} não está entre os eleitores: a votação habilita só "
                "quem estava ativo no clube quando ela começou."
            )

    def pendentes(self, confirmados: Iterable[MembroId]) -> frozenset[MembroId]:
        """Os eleitores que ainda não confirmaram a cédula do turno atual."""
        return self._eleitores - frozenset(confirmados)

    def abrir_turno_seguinte(self) -> None:
        """Passa ao turno seguinte, que desfaz os empates do atual."""
        self.verificar_aberta()
        self._turno_atual += 1

    def encerrar(self, momento: datetime) -> None:
        """Termina a votação: não resta empate a desfazer."""
        self.verificar_aberta()
        self._encerrada_em = momento
