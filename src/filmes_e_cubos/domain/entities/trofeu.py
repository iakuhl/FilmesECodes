"""Entidade que representa o troféu emitido ao vencedor de uma categoria do Óscar."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
    TrofeuId,
)


class Trofeu:
    """O resultado de uma categoria: a nomeação vencedora e quem leva o troféu.

    Sem nomeação vencedora (`None`) num empate absoluto, quando o troféu vai
    para um membro escolhido pelo grupo (decisões 8.6 e 29 de
    docs/PENDENCIAS.md).
    """

    def __init__(
        self,
        *,
        id: TrofeuId,
        categoria_id: CategoriaOscarId,
        nomeacao_vencedora_id: NomeacaoOscarId | None,
        membro_vencedor_id: MembroId,
        data_apuracao: date,
    ) -> None:
        self._id = id
        self._categoria_id = categoria_id
        self._nomeacao_vencedora_id = nomeacao_vencedora_id
        self._membro_vencedor_id = membro_vencedor_id
        self._data_apuracao = data_apuracao

    @classmethod
    def emitir(
        cls,
        *,
        categoria_id: CategoriaOscarId,
        nomeacao_vencedora_id: NomeacaoOscarId | None,
        membro_vencedor_id: MembroId,
        data_apuracao: date,
    ) -> Trofeu:
        return cls(
            id=TrofeuId(uuid4()),
            categoria_id=categoria_id,
            nomeacao_vencedora_id=nomeacao_vencedora_id,
            membro_vencedor_id=membro_vencedor_id,
            data_apuracao=data_apuracao,
        )

    @property
    def id(self) -> TrofeuId:
        return self._id

    @property
    def categoria_id(self) -> CategoriaOscarId:
        return self._categoria_id

    @property
    def nomeacao_vencedora_id(self) -> NomeacaoOscarId | None:
        return self._nomeacao_vencedora_id

    @property
    def membro_vencedor_id(self) -> MembroId:
        return self._membro_vencedor_id

    @property
    def data_apuracao(self) -> date:
        return self._data_apuracao
