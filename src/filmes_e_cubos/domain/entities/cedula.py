"""Entidade que representa a cédula de um eleitor num turno da votação do Óscar."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.oscar import (
    CedulaConfirmadaError,
    CedulaIncompletaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    CedulaId,
    MembroId,
    NomeacaoOscarId,
    VotacaoOscarId,
)


class Cedula:
    """As escolhas de um eleitor num turno da votação, categoria por categoria.

    O eleitor vota em cada categoria do turno e pode trocar os votos à
    vontade até confirmar a cédula; confirmada, ela não muda mais
    (decisão 25). O conteúdo é secreto: fica guardado, mas nenhuma
    interface o exibe (decisão 26) — só se a cédula foi confirmada e em
    quantas categorias já tem voto.

    As escolhas de cada categoria já chegam conferidas pelo turno dela
    (`TurnoDeVotacao.conferir_escolhas`): a cédula não conhece as
    candidatas.
    """

    def __init__(
        self,
        *,
        id: CedulaId,
        votacao_id: VotacaoOscarId,
        turno: int,
        membro_id: MembroId,
        escolhas: Mapping[CategoriaOscarId, Sequence[NomeacaoOscarId]] | None = None,
        confirmada_em: datetime | None = None,
    ) -> None:
        self._id = id
        self._votacao_id = votacao_id
        self._turno = turno
        self._membro_id = membro_id
        self._escolhas = {
            categoria_id: tuple(escolhidas) for categoria_id, escolhidas in (escolhas or {}).items()
        }
        self._confirmada_em = confirmada_em

    @classmethod
    def criar(cls, *, votacao_id: VotacaoOscarId, turno: int, membro_id: MembroId) -> Cedula:
        return cls(
            id=CedulaId(uuid4()),
            votacao_id=votacao_id,
            turno=turno,
            membro_id=membro_id,
        )

    @property
    def id(self) -> CedulaId:
        return self._id

    @property
    def votacao_id(self) -> VotacaoOscarId:
        return self._votacao_id

    @property
    def turno(self) -> int:
        return self._turno

    @property
    def membro_id(self) -> MembroId:
        return self._membro_id

    @property
    def escolhas(self) -> dict[CategoriaOscarId, tuple[NomeacaoOscarId, ...]]:
        """As escolhas de cada categoria, em ordem de preferência (uma cópia)."""
        return dict(self._escolhas)

    @property
    def categorias_votadas(self) -> frozenset[CategoriaOscarId]:
        return frozenset(self._escolhas)

    @property
    def confirmada_em(self) -> datetime | None:
        return self._confirmada_em

    @property
    def confirmada(self) -> bool:
        return self._confirmada_em is not None

    def verificar_aberta(self) -> None:
        if self.confirmada:
            raise CedulaConfirmadaError("A cédula já foi confirmada: os votos não mudam mais.")

    def votar(self, categoria_id: CategoriaOscarId, escolhas: Sequence[NomeacaoOscarId]) -> None:
        """Registra o voto numa categoria, trocando o anterior, se havia."""
        self.verificar_aberta()
        self._escolhas[categoria_id] = tuple(escolhas)

    def confirmar(
        self, categorias_do_turno: Iterable[CategoriaOscarId], *, momento: datetime
    ) -> None:
        """Trava a cédula; exige voto em todas as categorias do turno."""
        self.verificar_aberta()
        faltando = frozenset(categorias_do_turno) - self.categorias_votadas
        if faltando:
            raise CedulaIncompletaError(
                f"A cédula ainda não tem voto em {len(faltando)} categoria(s) do turno."
            )
        self._confirmada_em = momento
