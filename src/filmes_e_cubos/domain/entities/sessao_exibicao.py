"""Entidade que representa a sessão em que o clube assistiu a um filme."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.exceptions.avaliacao import MembroAusenteNaSessaoError
from filmes_e_cubos.domain.value_objects.identificadores import (
    IndicacaoId,
    MembroId,
    SessaoExibicaoId,
)
from filmes_e_cubos.domain.value_objects.media_das_notas import MediaDasNotas


class SessaoExibicao:
    """A sessão em que o clube efetivamente assistiu ao filme sorteado.

    Guarda quem esteve presente — só essas pessoas avaliam o filme — e a
    média das notas recebidas, refeita a cada avaliação.
    """

    def __init__(
        self,
        *,
        id: SessaoExibicaoId,
        indicacao_id: IndicacaoId,
        data_sessao: date,
        membros_presentes: frozenset[MembroId],
        media_das_notas: MediaDasNotas | None = None,
    ) -> None:
        self._id = id
        self._indicacao_id = indicacao_id
        self._data_sessao = data_sessao
        self._membros_presentes = membros_presentes
        self._media_das_notas = media_das_notas

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

    @property
    def media_das_notas(self) -> MediaDasNotas | None:
        """Média das notas recebidas; `None` enquanto ninguém deu nota."""
        return self._media_das_notas

    def verificar_presenca(self, membro_id: MembroId) -> None:
        """Só quem esteve na sessão pode avaliá-la (decisão 4 de docs/PENDENCIAS.md)."""
        if membro_id not in self._membros_presentes:
            raise MembroAusenteNaSessaoError(
                f"Membro {membro_id} não esteve presente na sessão {self._id}."
            )

    def recalcular_media(self, avaliacoes: Iterable[Avaliacao]) -> None:
        """Refaz a média a partir das avaliações da sessão; dorminhocos ficam de fora.

        Refazer a partir de todas as avaliações, em vez de somar só a
        nova, deixa a média certa mesmo que uma gravação anterior tenha
        falhado no meio do caminho.
        """
        self._media_das_notas = MediaDasNotas.das_notas(
            avaliacao.nota for avaliacao in avaliacoes if avaliacao.nota is not None
        )
