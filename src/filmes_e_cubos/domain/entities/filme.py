"""Entidade que representa um filme indicado ou assistido pelo clube."""

from __future__ import annotations

from uuid import uuid4

from filmes_e_cubos.domain.exceptions.filme import (
    DuracaoFilmeInvalidaError,
    TituloFilmeObrigatorioError,
)
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId


class Filme:
    """Um filme do catálogo, que um clube pode indicar e assistir.

    Não pertence a um clube específico: o mesmo filme pode ser indicado em
    clubes diferentes. Dentro de um clube, porém, ele passa uma vez só —
    indicado uma vez, assistido uma vez (ver `IndicarFilme`).
    """

    def __init__(
        self,
        *,
        id: FilmeId,
        titulo: str,
        ano_lancamento: int | None = None,
        diretor: str | None = None,
        identificador_externo: str | None = None,
        duracao_minutos: int | None = None,
    ) -> None:
        if not titulo or not titulo.strip():
            raise TituloFilmeObrigatorioError("O título do filme é obrigatório.")
        if duracao_minutos is not None:
            _validar_duracao(duracao_minutos)
        self._id = id
        self._titulo = titulo
        self._ano_lancamento = ano_lancamento
        self._diretor = diretor
        self._identificador_externo = identificador_externo
        self._duracao_minutos = duracao_minutos

    @classmethod
    def criar(
        cls,
        *,
        titulo: str,
        ano_lancamento: int | None = None,
        diretor: str | None = None,
        identificador_externo: str | None = None,
        duracao_minutos: int | None = None,
    ) -> Filme:
        return cls(
            id=FilmeId(uuid4()),
            titulo=titulo,
            ano_lancamento=ano_lancamento,
            diretor=diretor,
            identificador_externo=identificador_externo,
            duracao_minutos=duracao_minutos,
        )

    @property
    def id(self) -> FilmeId:
        return self._id

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def ano_lancamento(self) -> int | None:
        return self._ano_lancamento

    @property
    def diretor(self) -> str | None:
        return self._diretor

    @property
    def identificador_externo(self) -> str | None:
        return self._identificador_externo

    @property
    def duracao_minutos(self) -> int | None:
        """Duração em minutos; `None` enquanto ninguém a informou."""
        return self._duracao_minutos

    def definir_duracao(self, duracao_minutos: int) -> None:
        """Informa (ou corrige) a duração — ex.: de um filme cadastrado antes do campo existir."""
        _validar_duracao(duracao_minutos)
        self._duracao_minutos = duracao_minutos


def _validar_duracao(duracao_minutos: int) -> None:
    if duracao_minutos <= 0:
        raise DuracaoFilmeInvalidaError(
            f"A duração do filme deve ser positiva, em minutos; recebido: {duracao_minutos}."
        )
