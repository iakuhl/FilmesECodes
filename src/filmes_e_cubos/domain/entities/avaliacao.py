"""Entidade que representa a nota de um membro para uma sessão assistida."""

from __future__ import annotations

from uuid import uuid4

from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.identificadores import (
    AvaliacaoId,
    MembroId,
    SessaoExibicaoId,
)
from filmes_e_cubos.domain.value_objects.nota import Nota


class Avaliacao:
    """A nota (e comentário opcional) que um membro dá a uma sessão assistida."""

    def __init__(
        self,
        *,
        id: AvaliacaoId,
        sessao_id: SessaoExibicaoId,
        membro_id: MembroId,
        nota: Nota,
        comentario: str | None = None,
    ) -> None:
        self._id = id
        self._sessao_id = sessao_id
        self._membro_id = membro_id
        self._nota = nota
        self._comentario = comentario

    @classmethod
    def criar(
        cls,
        *,
        sessao_id: SessaoExibicaoId,
        membro_id: MembroId,
        nota: Nota,
        escala: EscalaAvaliacao,
        comentario: str | None = None,
    ) -> Avaliacao:
        """Cria uma avaliação, validando a nota contra a escala informada."""
        escala.validar(nota)
        return cls(
            id=AvaliacaoId(uuid4()),
            sessao_id=sessao_id,
            membro_id=membro_id,
            nota=nota,
            comentario=comentario,
        )

    @property
    def id(self) -> AvaliacaoId:
        return self._id

    @property
    def sessao_id(self) -> SessaoExibicaoId:
        return self._sessao_id

    @property
    def membro_id(self) -> MembroId:
        return self._membro_id

    @property
    def nota(self) -> Nota:
        return self._nota

    @property
    def comentario(self) -> str | None:
        return self._comentario
