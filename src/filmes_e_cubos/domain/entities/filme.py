"""Entidade que representa um filme indicado ou assistido pelo clube."""

from __future__ import annotations

from uuid import uuid4

from filmes_e_cubos.domain.exceptions.filme import TituloFilmeObrigatorioError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId


class Filme:
    """Um filme, potencialmente indicado e assistido em uma ou mais sessões.

    Não pertence a um clube específico: o mesmo filme pode, em tese, ser
    indicado em clubes diferentes numa futura versão multi-clube.
    """

    def __init__(
        self,
        *,
        id: FilmeId,
        titulo: str,
        ano_lancamento: int | None = None,
        diretor: str | None = None,
        identificador_externo: str | None = None,
    ) -> None:
        if not titulo or not titulo.strip():
            raise TituloFilmeObrigatorioError("O título do filme é obrigatório.")
        self._id = id
        self._titulo = titulo
        self._ano_lancamento = ano_lancamento
        self._diretor = diretor
        self._identificador_externo = identificador_externo

    @classmethod
    def criar(
        cls,
        *,
        titulo: str,
        ano_lancamento: int | None = None,
        diretor: str | None = None,
        identificador_externo: str | None = None,
    ) -> Filme:
        return cls(
            id=FilmeId(uuid4()),
            titulo=titulo,
            ano_lancamento=ano_lancamento,
            diretor=diretor,
            identificador_externo=identificador_externo,
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
