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
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao


class Avaliacao:
    """A nota (e comentário opcional) que um membro dá a uma sessão assistida,
    ou o registro de que o membro cochilou e não tem nota a dar (`DORMINHOCO`).
    """

    def __init__(
        self,
        *,
        id: AvaliacaoId,
        sessao_id: SessaoExibicaoId,
        membro_id: MembroId,
        status: StatusAvaliacao,
        nota: Nota | None = None,
        comentario: str | None = None,
    ) -> None:
        self._id = id
        self._sessao_id = sessao_id
        self._membro_id = membro_id
        self._status = status
        self._nota = nota
        self._comentario = comentario

    @classmethod
    def criar(
        cls,
        *,
        sessao_id: SessaoExibicaoId,
        membro_id: MembroId,
        escala: EscalaAvaliacao,
        nota: Nota | None = None,
        comentario: str | None = None,
    ) -> Avaliacao:
        """Cria uma avaliação. Sem `nota` (`None`), o membro cochilou e o
        status vira `DORMINHOCO`; com `nota`, ela é validada contra a
        escala informada e o status vira `NOTA_REGISTRADA`. Por construção,
        não existe forma de haver um status inconsistente com o valor de
        `nota`.
        """
        if nota is None:
            return cls(
                id=AvaliacaoId(uuid4()),
                sessao_id=sessao_id,
                membro_id=membro_id,
                status=StatusAvaliacao.DORMINHOCO,
                comentario=comentario,
            )
        escala.validar(nota)
        return cls(
            id=AvaliacaoId(uuid4()),
            sessao_id=sessao_id,
            membro_id=membro_id,
            status=StatusAvaliacao.NOTA_REGISTRADA,
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
    def status(self) -> StatusAvaliacao:
        return self._status

    @property
    def nota(self) -> Nota | None:
        return self._nota

    @property
    def comentario(self) -> str | None:
        return self._comentario
