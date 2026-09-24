"""Entidade que representa um membro do clube."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.membro import NomeMembroObrigatorioError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, MembroId


class Membro:
    """Uma pessoa do clube, que indica filmes e avalia sessões."""

    def __init__(
        self,
        *,
        id: MembroId,
        clube_id: ClubeId,
        nome: str,
        data_ingresso: date,
        apelido: str | None = None,
        ativo: bool = True,
    ) -> None:
        if not nome or not nome.strip():
            raise NomeMembroObrigatorioError("O nome do membro é obrigatório.")
        self._id = id
        self._clube_id = clube_id
        self._nome = nome
        self._apelido = apelido
        self._data_ingresso = data_ingresso
        self._ativo = ativo

    @classmethod
    def criar(
        cls,
        *,
        clube_id: ClubeId,
        nome: str,
        data_ingresso: date,
        apelido: str | None = None,
    ) -> Membro:
        return cls(
            id=MembroId(uuid4()),
            clube_id=clube_id,
            nome=nome,
            data_ingresso=data_ingresso,
            apelido=apelido,
        )

    @property
    def id(self) -> MembroId:
        return self._id

    @property
    def clube_id(self) -> ClubeId:
        return self._clube_id

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def apelido(self) -> str | None:
        return self._apelido

    @property
    def data_ingresso(self) -> date:
        return self._data_ingresso

    @property
    def ativo(self) -> bool:
        return self._ativo

    def desativar(self) -> None:
        """Marca o membro como inativo, preservando seu histórico."""
        self._ativo = False

    def reativar(self) -> None:
        """Reativa um membro previamente desativado."""
        self._ativo = True
