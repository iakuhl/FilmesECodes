"""Entidade que representa a disputa de uma categoria do Óscar num turno da votação."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Final
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.oscar import (
    NumeroDeNomeacoesInvalidoError,
    VotacaoEncerradaError,
    VotoInvalidoError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    NomeacaoOscarId,
    TurnoDeVotacaoId,
)
from filmes_e_cubos.domain.value_objects.status import ModoDeVotacao

PONTOS_DA_VOTACAO_DUPLA: Final = (2, 1)
"""A 1ª opção vale 2 pontos; a 2ª, 1 (decisão 8.1)."""


class TurnoDeVotacao:
    """A disputa de uma categoria num turno da votação.

    As candidatas são nomeações, não filmes: o mesmo filme pode ocupar
    várias vagas da categoria (decisões 20 e 24). A ordem delas é a ordem
    em que as nomeações foram feitas, e é assim que aparecem na cédula.

    Apurar o turno grava a pontuação de cada candidata — o placar que só
    sai por e-mail, para quem monta a cerimônia (decisão 27) — e decide se
    a categoria precisa de um turno seguinte (decisão 28):

    - topo único: a categoria está decidida;
    - topo empatado entre parte das candidatas: turno de votação dupla só
      com as empatadas (decisão 8.4; numa classificação, interpretação 2);
    - todas empatadas numa votação dupla: turno de classificação com as
      mesmas (decisões 8.5 e 16);
    - todas empatadas numa classificação: empate absoluto — nenhuma vence,
      e a categoria também está decidida (decisão 8.6).

    A sequência sempre termina: a cada dois turnos, no máximo, o número de
    candidatas cai.
    """

    def __init__(
        self,
        *,
        id: TurnoDeVotacaoId,
        categoria_id: CategoriaOscarId,
        numero: int,
        modo: ModoDeVotacao,
        candidatas: Sequence[NomeacaoOscarId],
        pontuacao: Sequence[int] | None = None,
        apurado_em: datetime | None = None,
    ) -> None:
        candidatas = tuple(candidatas)
        if len(candidatas) < 2 or len(set(candidatas)) != len(candidatas):
            raise NumeroDeNomeacoesInvalidoError(
                "Um turno de votação precisa de ao menos 2 nomeações distintas."
            )
        self._id = id
        self._categoria_id = categoria_id
        self._numero = numero
        self._modo = modo
        self._candidatas = candidatas
        self._pontuacao = tuple(pontuacao) if pontuacao is not None else None
        self._apurado_em = apurado_em

    @classmethod
    def abrir_primeiro(
        cls, *, categoria_id: CategoriaOscarId, candidatas: Sequence[NomeacaoOscarId]
    ) -> TurnoDeVotacao:
        """O 1º turno da categoria: votação dupla entre todas as nomeações."""
        return cls(
            id=TurnoDeVotacaoId(uuid4()),
            categoria_id=categoria_id,
            numero=1,
            modo=ModoDeVotacao.DUPLA,
            candidatas=candidatas,
        )

    @property
    def id(self) -> TurnoDeVotacaoId:
        return self._id

    @property
    def categoria_id(self) -> CategoriaOscarId:
        return self._categoria_id

    @property
    def numero(self) -> int:
        return self._numero

    @property
    def modo(self) -> ModoDeVotacao:
        return self._modo

    @property
    def candidatas(self) -> tuple[NomeacaoOscarId, ...]:
        return self._candidatas

    @property
    def pontuacao(self) -> tuple[int, ...] | None:
        """Os pontos de cada candidata, na ordem delas; `None` antes da apuração."""
        return self._pontuacao

    @property
    def apurado_em(self) -> datetime | None:
        return self._apurado_em

    @property
    def aberto(self) -> bool:
        return self._pontuacao is None

    @property
    def lideres(self) -> tuple[NomeacaoOscarId, ...]:
        """As candidatas com a maior pontuação; vazio enquanto o turno está aberto."""
        if self._pontuacao is None:
            return ()
        topo = max(self._pontuacao)
        return tuple(
            candidata
            for candidata, pontos in zip(self._candidatas, self._pontuacao, strict=True)
            if pontos == topo
        )

    @property
    def empate_absoluto(self) -> bool:
        """Todas empataram numa classificação: nenhuma vence (decisão 8.6)."""
        return self._modo is ModoDeVotacao.CLASSIFICACAO and len(self.lideres) == len(
            self._candidatas
        )

    def conferir_escolhas(self, escolhas: Sequence[NomeacaoOscarId]) -> tuple[NomeacaoOscarId, ...]:
        """Confere um voto e o devolve como tupla, em ordem de preferência.

        Na votação dupla, são duas nomeações diferentes (que podem ser do
        mesmo filme); na classificação, a ordem completa das candidatas.
        """
        escolhas = tuple(escolhas)
        for escolha in escolhas:
            if escolha not in self._candidatas:
                raise VotoInvalidoError(
                    f"A nomeação {escolha} não concorre neste turno da categoria."
                )
        if len(set(escolhas)) != len(escolhas):
            raise VotoInvalidoError("Cada nomeação aparece uma vez só no voto.")
        if self._modo is ModoDeVotacao.DUPLA and len(escolhas) != len(PONTOS_DA_VOTACAO_DUPLA):
            raise VotoInvalidoError(
                "Na votação dupla, o voto tem duas nomeações diferentes: a 1ª e a 2ª opção."
            )
        if self._modo is ModoDeVotacao.CLASSIFICACAO and len(escolhas) != len(self._candidatas):
            raise VotoInvalidoError(
                "Na votação por classificação, o voto ordena todas as "
                f"{len(self._candidatas)} nomeações do turno."
            )
        return escolhas

    def apurar(
        self, votos: Iterable[Sequence[NomeacaoOscarId]], *, momento: datetime
    ) -> TurnoDeVotacao | None:
        """Conta os votos e devolve o turno seguinte, se o topo empatou.

        Devolve `None` quando a categoria se decidiu — por um topo único ou
        por empate absoluto.
        """
        if not self.aberto:
            raise VotacaoEncerradaError("Este turno da categoria já foi apurado.")
        pesos = self._pesos()
        pontos = dict.fromkeys(self._candidatas, 0)
        for voto in votos:
            for escolha, peso in zip(self.conferir_escolhas(voto), pesos, strict=True):
                pontos[escolha] += peso
        self._pontuacao = tuple(pontos[candidata] for candidata in self._candidatas)
        self._apurado_em = momento
        return self._turno_seguinte()

    def _pesos(self) -> tuple[int, ...]:
        if self._modo is ModoDeVotacao.DUPLA:
            return PONTOS_DA_VOTACAO_DUPLA
        return tuple(range(len(self._candidatas), 0, -1))

    def _turno_seguinte(self) -> TurnoDeVotacao | None:
        lideres = self.lideres
        if len(lideres) == 1 or self.empate_absoluto:
            return None
        todas_empataram = len(lideres) == len(self._candidatas)
        return TurnoDeVotacao(
            id=TurnoDeVotacaoId(uuid4()),
            categoria_id=self._categoria_id,
            numero=self._numero + 1,
            modo=ModoDeVotacao.CLASSIFICACAO if todas_empataram else ModoDeVotacao.DUPLA,
            candidatas=lideres,
        )
